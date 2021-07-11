#
import os
import tensorflow as tf

from tensorflow.python.framework import ops
from tensorflow.python.framework import dtypes
from tensorflow_io.bigquery import BigQueryClient
from tensorflow_io.bigquery import BigQueryReadSession

# Model training constants.
# Virtual epochs design pattern:
# https://medium.com/google-cloud/ml-design-pattern-3-virtual-epochs-f842296de730
N_TRAIN_EXAMPLES = 2638
N_DEV_EXAMPLES = 353
STOP_POINT = 2.0
TOTAL_TRAIN_EXAMPLES = int(STOP_POINT * N_TRAIN_EXAMPLES)
BATCH_SIZE = 16
N_CHECKPOINTS = 2
STEPS_PER_EPOCH = (TOTAL_TRAIN_EXAMPLES // (BATCH_SIZE*N_CHECKPOINTS))


training_data_uri = os.environ["AIP_TRAINING_DATA_URI"]
validation_data_uri = os.environ["AIP_VALIDATION_DATA_URI"]
test_data_uri = os.environ["AIP_TEST_DATA_URI"]
data_format = os.environ["AIP_DATA_FORMAT"]

NUMERIC_FEATURES = [
    "customer_id",
    "n_purchases",
    "avg_purchase_size",
    "avg_purchase_revenue",
    "customer_age",
    "days_since_last_purchase",
    "target_monetary_value_3M",
]

CATEGORICAL_FEATURES = [
    "customer_country"
]

LABEL = "target_monetary_value_3M"


def caip_uri_to_fields(uri):
    uri = uri[5:]
    project, dataset, table = uri.split('.')
    return project, dataset, table


def features_and_labels(row_data):
    label = row_data.pop(LABEL)
    features = row_data
    return features, label


def read_bigquery(project, dataset, table):
    tensorflow_io_bigquery_client = BigQueryClient()
    read_session = tensorflow_io_bigquery_client.read_session(
      parent="projects/" + project,
      project_id=project, 
      dataset_id=dataset,
      table_id=table,
      selected_fields=NUMERIC_FEATURES + [LABEL],
      output_types=[dtypes.float64] * 7 + [dtypes.string],
      requested_streams=2)
    dataset = read_session.parallel_read_rows()
    transformed_ds = dataset.map(features_and_labels)
    return transformed_ds

BATCH_SIZE = 16

training_ds = read_bigquery(*caip_uri_to_fields(training_data_uri)).prefetch(1).shuffle(BATCH_SIZE*10).batch(BATCH_SIZE)
eval_ds = read_bigquery(*caip_uri_to_fields(validation_data_uri)).prefetch(1).shuffle(BATCH_SIZE*10).batch(BATCH_SIZE)
test_ds = read_bigquery(*caip_uri_to_fields(test_data_uri)).prefetch(1).shuffle(BATCH_SIZE*10).batch(BATCH_SIZE)


feature_columns = {
    feature: tf.feature_column.numeric_column(feature)
    for feature in NUMERIC_FEATURES
}


# Create a custom evalution metric.
def rmse(y_true, y_pred):
    return tf.sqrt(tf.reduce_mean(tf.square(y_pred - y_true)))


def build_model():
    """
    """
    model = tf.keras.Sequential([
        tf.keras.layers.DenseFeatures(feature_columns.values()),
        tf.keras.layers.Dense(64, activation=tf.nn.relu),
        tf.keras.layers.Dense(64, activation=tf.nn.relu),
        tf.keras.layers.Dense(1)
    ])
    
    optimizer = tf.keras.optimizers.Adam(0.001)
    
    tensorboard_callback = tf.keras.callbacks.TensorBoard(
#         log_dir=os.environ['AIP_TENSORBOARD_LOG_DIR'],
        log_dir=os.environ["AIP_MODEL_DIR"] + '/tensorboard-logs',
        histogram_freq=1)
    
    earlystopping_callback = tf.keras.callbacks.EarlyStopping(patience=2)
    
    checkpoint_callback = tf.keras.callbacks.ModelCheckpoint(
        filepath=os.environ["AIP_MODEL_DIR"] + '/checkpoints',
        save_weights_only=True,
        monitor='val_loss',
        mode='min')    
    
    model.compile(loss='mse',
                  optimizer=optimizer,
                  callbacks=[[tensorboard_callback, 
                              earlystopping_callback,
                              checkpoint_callback]],
                  metrics=[['mae', 'mse', rmse]])
    
    return model

model = build_model()

model.fit(training_ds,
          validation_data=eval_ds,
          steps_per_epoch=STEPS_PER_EPOCH,
          epochs=N_CHECKPOINTS,
          callbacks=[tensorboard_callback])

print(model.evaluate(test_ds))

# rankdir='LR' is used to make the graph horizontal.
# tf.keras.utils.plot_model(model, show_shapes=True, rankdir="LR")

tf.saved_model.save(model, os.environ["AIP_MODEL_DIR"])
