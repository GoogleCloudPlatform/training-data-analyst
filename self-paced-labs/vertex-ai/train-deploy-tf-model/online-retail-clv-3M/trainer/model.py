import os
import logging
import tempfile
import tensorflow as tf
from explainable_ai_sdk.metadata.tf.v2 import SavedModelMetadataBuilder
from tensorflow.python.framework import dtypes
from tensorflow_io.bigquery import BigQueryClient
from tensorflow_io.bigquery import BigQueryReadSession


# Model feature constants.
NUMERIC_FEATURES = [
    "n_purchases",
    "avg_purchase_size",
    "avg_purchase_revenue",
    "customer_age",
    "days_since_last_purchase",
]

CATEGORICAL_FEATURES = [
    "customer_country"
]

LABEL = "target_monetary_value_3M"


def caip_uri_to_fields(uri):
    """Helper function to parse BQ URI."""
    # Remove bq:// prefix.
    uri = uri[5:]
    project, dataset, table = uri.split('.')
    return project, dataset, table


def features_and_labels(row_data):
    """Helper feature and label mapping function for tf.data."""
    label = row_data.pop(LABEL)
    features = row_data
    return features, label


def read_bigquery(project, dataset, table):
    """TensorFlow IO BigQuery Reader."""
    tensorflow_io_bigquery_client = BigQueryClient()
    read_session = tensorflow_io_bigquery_client.read_session(
      parent="projects/" + project,
      project_id=project, 
      dataset_id=dataset,
      table_id=table,
      # Pass list of features and label to be selected from BQ.
      selected_fields=NUMERIC_FEATURES + [LABEL],
      # Provide output TensorFlow data types for features and label.
      output_types=[dtypes.int64, dtypes.float64, dtypes.float64, dtypes.int64, dtypes.int64] + [dtypes.float64],
      requested_streams=2)
    dataset = read_session.parallel_read_rows()
    transformed_ds = dataset.map(features_and_labels)
    return transformed_ds


def rmse(y_true, y_pred):
    """Custom RMSE regression metric."""
    return tf.sqrt(tf.reduce_mean(tf.square(y_pred - y_true)))


def build_model(hparams):
    """Build and compile a TensorFlow Keras DNN Regressor."""

    feature_columns = [
        tf.feature_column.numeric_column(key=feature)
        for feature in NUMERIC_FEATURES
    ]
    
    input_layers = {
        feature.key: tf.keras.layers.Input(name=feature.key, shape=(), dtype=tf.float32)
        for feature in feature_columns
    }
    # Keras Functional API: https://keras.io/guides/functional_api
    inputs = tf.keras.layers.DenseFeatures(feature_columns, name='inputs')(input_layers)
    d1 = tf.keras.layers.Dense(256, activation=tf.nn.relu, name='d1')(inputs)
    d2 = tf.keras.layers.Dropout(hparams['dropout'], name='d2')(d1)    
    # Note: a single neuron scalar output for regression.
    output = tf.keras.layers.Dense(1, name='output')(d2)
    
    model = tf.keras.Model(input_layers, output, name='online-retail-clv')
    
    optimizer = tf.keras.optimizers.Adam(hparams['learning-rate'])    
    
    # Note: MAE loss is more resistant to outliers than MSE.
    model.compile(loss=tf.keras.losses.MAE,
                  optimizer=optimizer,
                  metrics=[['mae', 'mse', rmse]])
    
    return model


def train_evaluate_explain_model(hparams):
    """Train, evaluate, explain TensorFlow Keras DNN Regressor.
    Args:
      hparams(dict): A dictionary containing model training arguments.
    Returns:
      history(tf.keras.callbacks.History): Keras callback that records training event history.
    """
    training_ds = read_bigquery(*caip_uri_to_fields(hparams['training-data-uri'])).prefetch(1).shuffle(hparams['batch-size']*10).batch(hparams['batch-size']).repeat()
    eval_ds = read_bigquery(*caip_uri_to_fields(hparams['validation-data-uri'])).prefetch(1).shuffle(hparams['batch-size']*10).batch(hparams['batch-size'])
    test_ds = read_bigquery(*caip_uri_to_fields(hparams['test-data-uri'])).prefetch(1).shuffle(hparams['batch-size']*10).batch(hparams['batch-size'])
    
    model = build_model(hparams)
    logging.info(model.summary())
    
    tensorboard_callback = tf.keras.callbacks.TensorBoard(
        log_dir=hparams['tensorboard-dir'],
        histogram_freq=1)
    
    # Reduce overfitting and shorten training times.
    earlystopping_callback = tf.keras.callbacks.EarlyStopping(patience=2)
    
    # Ensure your training job's resilience to VM restarts.
    checkpoint_callback = tf.keras.callbacks.ModelCheckpoint(
        filepath= hparams['checkpoint-dir'],
        save_weights_only=True,
        monitor='val_loss',
        mode='min')
    
    # Virtual epochs design pattern:
    # https://medium.com/google-cloud/ml-design-pattern-3-virtual-epochs-f842296de730
    TOTAL_TRAIN_EXAMPLES = int(hparams['stop-point'] * hparams['n-train-examples'])
    STEPS_PER_EPOCH = (TOTAL_TRAIN_EXAMPLES // (hparams['batch-size']*hparams['n-checkpoints']))    
    
    history = model.fit(training_ds,
                        validation_data=eval_ds,
                        steps_per_epoch=STEPS_PER_EPOCH,
                        epochs=hparams['n-checkpoints'],
                        callbacks=[[tensorboard_callback,
                                    earlystopping_callback,
                                    checkpoint_callback]])
    
    logging.info(model.evaluate(test_ds))
    
    # Create a temp directory to save intermediate TF SavedModel prior to Explainable metadata creation.
    tmpdir = tempfile.mkdtemp()
    
    # Export Keras model in TensorFlow SavedModel format.
    model.save(tmpdir)
    
    # Annotate and save TensorFlow SavedModel with Explainable metadata to GCS.
    builder = SavedModelMetadataBuilder(tmpdir)
    builder.save_model_with_metadata(hparams['model-dir'])
    
    return history
