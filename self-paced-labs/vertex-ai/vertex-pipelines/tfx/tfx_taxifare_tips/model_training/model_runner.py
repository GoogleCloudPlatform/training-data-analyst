"""A run_fn method called by the TFX Trainer component."""

import os
import logging
from tfx import v1 as tfx
from tfx_taxifare_tips.model_training import defaults
from tfx_taxifare_tips.model_training import model_trainer
from tfx_taxifare_tips.model_training import model_exporter


# TFX Trainer will call this function.
def run_fn(fn_args: tfx.components.FnArgs):
    """Train the model based on given args.
    Args:
      fn_args: Holds args used to train the model as name/value pairs. See
      https://www.tensorflow.org/tfx/api_docs/python/tfx/v1/components/FnArgs.
    """
    logging.info("Model Runner started...")
    logging.info("fn_args: %s", fn_args)
    logging.info("")

    try:
        log_dir = fn_args.model_run_dir
    except KeyError:
        log_dir = os.path.join(os.path.dirname(fn_args.serving_model_dir), "logs")

    hyperparameters = fn_args.hyperparameters
    if not hyperparameters:
        hyperparameters = {}

    hyperparameters = defaults.update_hyperparameters(hyperparameters)
    logging.info("Hyperparameter:")
    logging.info(hyperparameters)
    logging.info("")

    logging.info("Model Runner executing model trainer...")
    classifier = model_trainer.train(
        data_accessor=fn_args.data_accessor,
        train_data_dir=fn_args.train_files,
        eval_data_dir=fn_args.eval_files,
        tft_output_dir=fn_args.transform_output,
        log_dir=log_dir,
        hyperparameters=hyperparameters,
    )

    logging.info("Model Runner executing model evaluation...")
    classifier = model_trainer.evaluate(
        classifier=classifier,
        data_accessor=fn_args.data_accessor,
        eval_data_dir=fn_args.eval_files,
        tft_output_dir=fn_args.transform_output,
        hyperparameters=hyperparameters,
    )

    logging.info("Model Runner executing exporter...")
    model_exporter.export_serving_model(
        classifier=classifier,
        serving_model_dir=fn_args.serving_model_dir,
        raw_schema_location=fn_args.schema_path,
        tft_output_dir=fn_args.transform_output,
    )
    logging.info("Model Runner completed.")
