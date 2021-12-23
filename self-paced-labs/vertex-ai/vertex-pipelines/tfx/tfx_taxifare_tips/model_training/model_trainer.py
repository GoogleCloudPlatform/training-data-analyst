"""Train and evaluate the model."""
import logging
import tensorflow as tf
import tensorflow_transform as tft

from tfx_taxifare_tips.model_training import model_input
from tfx_taxifare_tips.model_training import model


def train(
    data_accessor,
    train_data_dir,
    eval_data_dir,
    tft_output_dir,
    log_dir,
    hyperparameters,
):
    """
    Args:
      data_accessor:
      train_data_dir:
      eval_data_dir:
      tft_output_dir:
      log_dir:
      hyperparameters:
    Returns:
      classifer:
    """

    logging.info("Loading tft output from %s", tft_output_dir)
    tft_output = tft.TFTransformOutput(tft_output_dir)
    schema = tft_output.transformed_metadata.schema

    train_dataset = model_input.get_dataset(
        file_pattern=train_data_dir,
        data_accessor=data_accessor,
        schema=schema,
        batch_size=hyperparameters["batch_size"],
    )

    eval_dataset = model_input.get_dataset(
        file_pattern=eval_data_dir,
        data_accessor=data_accessor,
        schema=schema,
        batch_size=hyperparameters["batch_size"],
    )

    classifier = model.build_binary_classifier(
        hyperparameters=hyperparameters, tft_output=tft_output
    )

    optimizer = tf.keras.optimizers.Adam(learning_rate=hyperparameters["learning_rate"])
    loss = tf.keras.losses.BinaryCrossentropy(from_logits=True)
    metrics = [tf.keras.metrics.BinaryAccuracy(name="accuracy")]

    classifier.compile(optimizer=optimizer, loss=loss, metrics=metrics)

    classifier.summary(print_fn=logging.info)

    tensorboard_callback = tf.keras.callbacks.TensorBoard(log_dir=log_dir)

    early_stopping_callback = tf.keras.callbacks.EarlyStopping(
        monitor="val_loss", patience=2, restore_best_weights=True
    )

    logging.info("Model training started...")
    classifier.fit(
        train_dataset,
        epochs=hyperparameters["num_epochs"],
        validation_data=eval_dataset,
        callbacks=[tensorboard_callback, early_stopping_callback],
    )
    logging.info("Model training completed.")

    return classifier


def evaluate(classifier, data_accessor, eval_data_dir, tft_output_dir, hyperparameters):
    """
    Args:
      classifier:
      data_accessor:
      eval_data_dir:
      tft_output_dir:
      hyperparameters:
    Returns:
      evaluation_metrics:
    """
    logging.info("Loading tft output from %s", tft_output_dir)
    tft_output = tft.TFTransformOutput(tft_output_dir)
    schema = tft_output.transformed_metadata.schema

    logging.info("Model evaluation started...")
    eval_dataset = model_input.get_dataset(
        file_pattern=eval_data_dir,
        data_accessor=data_accessor,
        schema=schema,
        batch_size=hyperparameters["batch_size"],
    )

    evaluation_metrics = classifier.evaluate(eval_dataset)
    logging.info("Model evaluation completed.")

    return evaluation_metrics
