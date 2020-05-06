import datetime
import logging
import os
import shutil

import numpy as np
import tensorflow as tf

from tensorflow.keras import activations
from tensorflow.keras import callbacks
from tensorflow.keras import layers
from tensorflow.keras import models

from tensorflow import feature_column as fc

logging.info(tf.version.VERSION)


CSV_COLUMNS = [
        'fare_amount',
        'pickup_datetime',
        'pickup_longitude',
        'pickup_latitude',
        'dropoff_longitude',
        'dropoff_latitude',
        'passenger_count',
        'key',
]
LABEL_COLUMN = 'fare_amount'
DEFAULTS = [[0.0], ['na'], [0.0], [0.0], [0.0], [0.0], [0.0], ['na']]
DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']


def features_and_labels(row_data):
    for unwanted_col in ['key']:
        row_data.pop(unwanted_col)
    label = row_data.pop(LABEL_COLUMN)
    return row_data, label


def load_dataset(pattern, batch_size, num_repeat):
    dataset = tf.data.experimental.make_csv_dataset(
        file_pattern=pattern,
        batch_size=batch_size,
        column_names=CSV_COLUMNS,
        column_defaults=DEFAULTS,
        num_epochs=num_repeat,
    )
    return dataset.map(features_and_labels)


def create_train_dataset(pattern, batch_size):
    dataset = load_dataset(pattern, batch_size, num_repeat=None)
    return dataset.prefetch(1)


def create_eval_dataset(pattern, batch_size):
    dataset = load_dataset(pattern, batch_size, num_repeat=1)
    return dataset.prefetch(1)


def parse_datetime(s):
    if type(s) is not str:
        s = s.numpy().decode('utf-8')
    return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S %Z")


def euclidean(params):
    lon1, lat1, lon2, lat2 = params
    londiff = lon2 - lon1
    latdiff = lat2 - lat1
    return tf.sqrt(londiff*londiff + latdiff*latdiff)


def get_dayofweek(s):
    ts = parse_datetime(s)
    return DAYS[ts.weekday()]


@tf.function
def dayofweek(ts_in):
    return tf.map_fn(
        lambda s: tf.py_function(get_dayofweek, inp=[s], Tout=tf.string),
        ts_in
    )


@tf.function
def fare_thresh(x):
    return 60 * activations.relu(x)


def transform(inputs, NUMERIC_COLS, STRING_COLS, nbuckets):
    # Pass-through columns
    transformed = inputs.copy()
    del transformed['pickup_datetime']

    feature_columns = {
        colname: fc.numeric_column(colname)
        for colname in NUMERIC_COLS
    }

    # Scaling longitude from range [-70, -78] to [0, 1]
    for lon_col in ['pickup_longitude', 'dropoff_longitude']:
        transformed[lon_col] = layers.Lambda(
            lambda x: (x + 78)/8.0,
            name='scale_{}'.format(lon_col)
        )(inputs[lon_col])

    # Scaling latitude from range [37, 45] to [0, 1]
    for lat_col in ['pickup_latitude', 'dropoff_latitude']:
        transformed[lat_col] = layers.Lambda(
            lambda x: (x - 37)/8.0,
            name='scale_{}'.format(lat_col)
        )(inputs[lat_col])

    # Adding Euclidean dist (no need to be accurate: NN will calibrate it)
    transformed['euclidean'] = layers.Lambda(euclidean, name='euclidean')([
        inputs['pickup_longitude'],
        inputs['pickup_latitude'],
        inputs['dropoff_longitude'],
        inputs['dropoff_latitude']
    ])
    feature_columns['euclidean'] = fc.numeric_column('euclidean')

    # hour of day from timestamp of form '2010-02-08 09:17:00+00:00'
    transformed['hourofday'] = layers.Lambda(
        lambda x: tf.strings.to_number(
            tf.strings.substr(x, 11, 2), out_type=tf.dtypes.int32),
        name='hourofday'
    )(inputs['pickup_datetime'])
    feature_columns['hourofday'] = fc.indicator_column(
        fc.categorical_column_with_identity(
            'hourofday', num_buckets=24))

    latbuckets = np.linspace(0, 1, nbuckets).tolist()
    lonbuckets = np.linspace(0, 1, nbuckets).tolist()
    b_plat = fc.bucketized_column(
        feature_columns['pickup_latitude'], latbuckets)
    b_dlat = fc.bucketized_column(
            feature_columns['dropoff_latitude'], latbuckets)
    b_plon = fc.bucketized_column(
            feature_columns['pickup_longitude'], lonbuckets)
    b_dlon = fc.bucketized_column(
            feature_columns['dropoff_longitude'], lonbuckets)
    ploc = fc.crossed_column(
            [b_plat, b_plon], nbuckets * nbuckets)
    dloc = fc.crossed_column(
            [b_dlat, b_dlon], nbuckets * nbuckets)
    pd_pair = fc.crossed_column([ploc, dloc], nbuckets ** 4)
    feature_columns['pickup_and_dropoff'] = fc.embedding_column(
            pd_pair, 100)

    return transformed, feature_columns


def rmse(y_true, y_pred):
    return tf.sqrt(tf.reduce_mean(tf.square(y_pred - y_true)))


def build_dnn_model(nbuckets, nnsize, lr):
    STRING_COLS = ['pickup_datetime']
    NUMERIC_COLS = (
            set(CSV_COLUMNS) - set([LABEL_COLUMN, 'key']) - set(STRING_COLS)
    )
    inputs = {
        colname: layers.Input(name=colname, shape=(), dtype='float32')
        for colname in NUMERIC_COLS
    }
    inputs.update({
        colname: layers.Input(name=colname, shape=(), dtype='string')
        for colname in STRING_COLS
    })

    # transforms
    transformed, feature_columns = transform(
        inputs, NUMERIC_COLS, STRING_COLS, nbuckets=nbuckets)
    dnn_inputs = layers.DenseFeatures(feature_columns.values())(transformed)

    x = dnn_inputs
    for layer, nodes in enumerate(nnsize):
        x = layers.Dense(nodes, activation='relu', name='h{}'.format(layer))(x)
    output = layers.Dense(1, name='fare')(x)

    model = models.Model(inputs, output)
    lr_optimizer = tf.keras.optimizers.Adam(learning_rate=lr)
    model.compile(optimizer=lr_optimizer, loss='mse', metrics=[rmse, 'mse'])

    return model


def train_and_evaluate(hparams):
    batch_size = hparams['batch_size']
    nbuckets = hparams['nbuckets']
    lr = hparams['lr']
    nnsize = hparams['nnsize']
    eval_data_path = hparams['eval_data_path']
    num_evals = hparams['num_evals']
    num_examples_to_train_on = hparams['num_examples_to_train_on']
    output_dir = hparams['output_dir']
    train_data_path = hparams['train_data_path']

    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    savedmodel_dir = os.path.join(output_dir, 'export/savedmodel')
    model_export_path = os.path.join(savedmodel_dir, timestamp)
    checkpoint_path = os.path.join(output_dir, 'checkpoints')
    tensorboard_path = os.path.join(output_dir, 'tensorboard')

    if tf.io.gfile.exists(output_dir):
        tf.io.gfile.rmtree(output_dir)

    model = build_dnn_model(nbuckets, nnsize, lr)
    logging.info(model.summary())

    trainds = create_train_dataset(train_data_path, batch_size)
    evalds = create_eval_dataset(eval_data_path, batch_size)

    steps_per_epoch = num_examples_to_train_on // (batch_size * num_evals)

    checkpoint_cb = callbacks.ModelCheckpoint(
        checkpoint_path,
        save_weights_only=True,
        verbose=1
    )
    tensorboard_cb = callbacks.TensorBoard(tensorboard_path)

    history = model.fit(
        trainds,
        validation_data=evalds,
        epochs=num_evals,
        steps_per_epoch=max(1, steps_per_epoch),
        verbose=2,  # 0=silent, 1=progress bar, 2=one line per epoch
        callbacks=[checkpoint_cb, tensorboard_cb]
    )

    # Exporting the model with default serving function.
    tf.saved_model.save(model, model_export_path)
    return history
