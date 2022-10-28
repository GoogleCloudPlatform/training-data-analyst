"""Data prep, train and evaluate DNN model."""

import logging
import os

import numpy as np
import tensorflow as tf
from tensorflow.keras import callbacks, models
from tensorflow.keras.layers import (
    Concatenate,
    Dense,
    Discretization,
    Embedding,
    Flatten,
    Input,
    Lambda,
)
from tensorflow.keras.layers.experimental.preprocessing import HashedCrossing

logging.info(tf.version.VERSION)

CSV_COLUMNS = [
    "fare_amount",
    "pickup_datetime",
    "pickup_longitude",
    "pickup_latitude",
    "dropoff_longitude",
    "dropoff_latitude",
    "passenger_count",
    "key",
]

LABEL_COLUMN = "fare_amount"
DEFAULTS = [[0.0], ["na"], [0.0], [0.0], [0.0], [0.0], [0.0], ["na"]]
UNWANTED_COLS = ["pickup_datetime", "key"]

INPUT_COLS = [
    c for c in CSV_COLUMNS if c != LABEL_COLUMN and c not in UNWANTED_COLS
]


def features_and_labels(row_data):
    for unwanted_col in UNWANTED_COLS:
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
        shuffle_buffer_size=1000000,
    )
    return dataset.map(features_and_labels)


def create_train_dataset(pattern, batch_size):
    dataset = load_dataset(pattern, batch_size, num_repeat=None)
    return dataset.prefetch(1)


def create_eval_dataset(pattern, batch_size):
    dataset = load_dataset(pattern, batch_size, num_repeat=1)
    return dataset.prefetch(1)


def euclidean(params):
    lon1, lat1, lon2, lat2 = params
    londiff = lon2 - lon1
    latdiff = lat2 - lat1
    return tf.sqrt(londiff * londiff + latdiff * latdiff)


def scale_longitude(lon_column):
    return (lon_column + 78) / 8.0


def scale_latitude(lat_column):
    return (lat_column - 37) / 8.0


def transform(inputs, nbuckets):
    transformed = {}

    # Scaling longitude from range [-70, -78] to [0, 1]
    transformed["scaled_plon"] = Lambda(scale_longitude, name="scale_plon")(
        inputs["pickup_longitude"]
    )
    transformed["scaled_dlon"] = Lambda(scale_longitude, name="scale_dlon")(
        inputs["dropoff_longitude"]
    )

    # Scaling latitude from range [37, 45] to [0, 1]
    transformed["scaled_plat"] = Lambda(scale_latitude, name="scale_plat")(
        inputs["pickup_latitude"]
    )
    transformed["scaled_dlat"] = Lambda(scale_latitude, name="scale_dlat")(
        inputs["dropoff_latitude"]
    )

    # Apply euclidean function
    transformed["euclidean_distance"] = Lambda(euclidean, name="euclidean")(
        [
            inputs["pickup_longitude"],
            inputs["pickup_latitude"],
            inputs["dropoff_longitude"],
            inputs["dropoff_latitude"],
        ]
    )

    latbuckets = np.linspace(start=0.0, stop=1.0, num=nbuckets).tolist()
    lonbuckets = np.linspace(start=0.0, stop=1.0, num=nbuckets).tolist()

    # Bucketization with Discretization layer
    plon = Discretization(lonbuckets, name="plon_bkt")(
        transformed["scaled_plon"]
    )
    plat = Discretization(latbuckets, name="plat_bkt")(
        transformed["scaled_plat"]
    )
    dlon = Discretization(lonbuckets, name="dlon_bkt")(
        transformed["scaled_dlon"]
    )
    dlat = Discretization(latbuckets, name="dlat_bkt")(
        transformed["scaled_dlat"]
    )

    # Feature Cross with HashedCrossing layer
    p_fc = HashedCrossing(num_bins=nbuckets * nbuckets, name="p_fc")(
        (plon, plat)
    )
    d_fc = HashedCrossing(num_bins=nbuckets * nbuckets, name="d_fc")(
        (dlon, dlat)
    )
    pd_fc = HashedCrossing(num_bins=nbuckets**4, name="pd_fc")((p_fc, d_fc))

    # Embedding with Embedding layer
    transformed["pd_embed"] = Flatten()(
        Embedding(input_dim=nbuckets**4, output_dim=10, name="pd_embed")(
            pd_fc
        )
    )

    transformed["passenger_count"] = inputs["passenger_count"]

    return transformed


def rmse(y_true, y_pred):
    return tf.sqrt(tf.reduce_mean(tf.square(y_pred - y_true)))


def build_dnn_model(nbuckets, nnsize, lr):  # pylint: disable=unused-argument
    inputs = {
        colname: Input(name=colname, shape=(1,), dtype="float32")
        for colname in INPUT_COLS
    }

    # transforms
    transformed = transform(inputs, nbuckets)
    dnn_inputs = Concatenate()(transformed.values())

    x = dnn_inputs
    for layer, nodes in enumerate(nnsize):
        x = Dense(nodes, activation="relu", name=f"h{layer}")(x)
    output = Dense(1, name="fare")(x)

    model = models.Model(inputs, output)

    # TODO 1a: Your code here

    return model


def train_and_evaluate(hparams):
    # TODO 1b: Your code here

    nnsize = [int(s) for s in hparams["nnsize"].split()]
    eval_data_path = hparams["eval_data_path"]
    num_evals = hparams["num_evals"]
    num_examples_to_train_on = hparams["num_examples_to_train_on"]
    output_dir = hparams["output_dir"]
    train_data_path = hparams["train_data_path"]

    model_export_path = os.path.join(output_dir, "savedmodel")
    checkpoint_path = os.path.join(output_dir, "checkpoints")
    tensorboard_path = os.path.join(output_dir, "tensorboard")

    if tf.io.gfile.exists(output_dir):
        tf.io.gfile.rmtree(output_dir)

    model = build_dnn_model(
        nbuckets, nnsize, lr  # pylint: disable=undefined-variable
    )
    logging.info(model.summary())

    trainds = create_train_dataset(
        train_data_path, batch_size  # pylint: disable=undefined-variable
    )
    evalds = create_eval_dataset(
        eval_data_path, batch_size  # pylint: disable=undefined-variable
    )

    steps_per_epoch = num_examples_to_train_on // (
        batch_size * num_evals  # pylint: disable=undefined-variable
    )

    checkpoint_cb = callbacks.ModelCheckpoint(
        checkpoint_path, save_weights_only=True, verbose=1
    )
    tensorboard_cb = callbacks.TensorBoard(tensorboard_path, histogram_freq=1)

    history = model.fit(
        trainds,
        validation_data=evalds,
        epochs=num_evals,
        steps_per_epoch=max(1, steps_per_epoch),
        verbose=2,  # 0=silent, 1=progress bar, 2=one line per epoch
        callbacks=[checkpoint_cb, tensorboard_cb],
    )

    # Exporting the model with default serving function.
    model.save(model_export_path)
    return history
