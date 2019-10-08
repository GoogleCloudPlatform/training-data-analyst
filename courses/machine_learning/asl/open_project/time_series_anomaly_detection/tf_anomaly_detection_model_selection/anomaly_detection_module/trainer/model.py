import tensorflow as tf

from .anomaly_detection import anomaly_detection
from .input import read_dataset
from .serving import serving_input_fn

# Set logging to be level of INFO
tf.logging.set_verbosity(tf.logging.INFO)


def train_and_evaluate(args):
  """Train and evaluate custom Estimator with three training modes.

  Given the dictionary of parameters, create custom Estimator and run up to
  three training modes then return Estimator object.

  Args:
    args: Dictionary of parameters.

  Returns:
    Estimator object.
  """
  # Create our custom estimator using our model function
  estimator = tf.estimator.Estimator(
      model_fn=anomaly_detection,
      model_dir=args["output_dir"],
      params={key: val for key, val in args.items()})

  if args["training_mode"] == "reconstruction":
    # Calculate max_steps
    max_steps = int(args["reconstruction_epochs"] * args["train_examples"])
    max_steps = max_steps // args["train_batch_size"]
    max_steps += args["previous_train_steps"]
    
    # Create eval spec to read in our validation data
    eval_spec = tf.estimator.EvalSpec(
        input_fn=read_dataset(
            filename=args["eval_file_pattern"],
            mode=tf.estimator.ModeKeys.EVAL,
            batch_size=args["eval_batch_size"],
            params=args),
        steps=None,
        start_delay_secs=args["start_delay_secs"],  # start eval after N secs
        throttle_secs=args["throttle_secs"])  # evaluate every N secs

    if args["model_type"] == "pca":
      # Create train spec to read in our training data
      train_spec = tf.estimator.TrainSpec(
          input_fn=read_dataset(
              filename=args["train_file_pattern"],
              mode=tf.estimator.ModeKeys.EVAL,  # read through train data once
              batch_size=args["train_batch_size"],
              params=args),
          max_steps=max_steps)
      # Check to see if we need to additionally tune principal components
      if not args["autotune_principal_components"]:
        # Create train and evaluate loop to train and evaluate our estimator
        tf.estimator.train_and_evaluate(
            estimator=estimator, train_spec=train_spec, eval_spec=eval_spec)
      else:
          if (args["k_principal_components_time"] is None or
              args["k_principal_components_feat"] is None):
            # Create train and evaluate loop to train and evaluate our estimator
            tf.estimator.train_and_evaluate(
                estimator=estimator, train_spec=train_spec, eval_spec=eval_spec)
    else:  # dense_autoencoder or lstm_enc_dec_autoencoder
      # Create early stopping hook to help reduce overfitting
      early_stopping_hook = tf.contrib.estimator.stop_if_no_decrease_hook(
          estimator=estimator,
          metric_name="rmse",
          max_steps_without_decrease=100,
          min_steps=1000,
          run_every_secs=60,
          run_every_steps=None)

      # Create train spec to read in our training data
      train_spec = tf.estimator.TrainSpec(
          input_fn=read_dataset(
              filename=args["train_file_pattern"],
              mode=tf.estimator.ModeKeys.TRAIN,
              batch_size=args["train_batch_size"],
              params=args),
          max_steps=max_steps,
          hooks=[early_stopping_hook])

      # Create train and evaluate loop to train and evaluate our estimator
      tf.estimator.train_and_evaluate(
          estimator=estimator, train_spec=train_spec, eval_spec=eval_spec)
  else:
    # Calculate max_steps
    max_steps = args["train_examples"] // args["train_batch_size"]
    max_steps += args["previous_train_steps"]

    # if args["training_mode"] == "calculate_error_distribution_statistics"
    # Get final mahalanobis statistics over the entire val_1 dataset

    # if args["training_mode"] == "tune_anomaly_thresholds"
    # Tune anomaly thresholds using val_2 and val_anom datasets
    train_spec = tf.estimator.TrainSpec(
        input_fn=read_dataset(
            filename=args["train_file_pattern"],
            mode=tf.estimator.ModeKeys.EVAL,  # read through val data once
            batch_size=args["train_batch_size"],
            params=args),
        max_steps=max_steps)

    if args["training_mode"] == "calculate_error_distribution_statistics":
      # Don't create exporter for serving yet since anomaly thresholds
      # aren't trained yet
      exporter = None
    elif args["training_mode"] == "tune_anomaly_thresholds":
      # Create exporter that uses serving_input_fn to create saved_model
      # for serving
      exporter = tf.estimator.LatestExporter(
          name="exporter",
          serving_input_receiver_fn=lambda: serving_input_fn(
              args["feat_names"], args["seq_len"]))
    else:
      print("{0} isn't a valid training mode!".format(args["training_mode"]))

    # Create eval spec to read in our validation data and export our model
    eval_spec = tf.estimator.EvalSpec(
        input_fn=read_dataset(
            filename=args["eval_file_pattern"],
            mode=tf.estimator.ModeKeys.EVAL,
            batch_size=args["eval_batch_size"],
            params=args),
        steps=None,
        exporters=exporter,
        start_delay_secs=args["start_delay_secs"],  # start eval after N secs
        throttle_secs=args["throttle_secs"])  # evaluate every N secs

  if (args["training_mode"] == "calculate_error_distribution_statistics" or
      args["training_mode"] == "tune_anomaly_thresholds"):
    # Create train and evaluate loop to train and evaluate our estimator
    tf.estimator.train_and_evaluate(
        estimator=estimator, train_spec=train_spec, eval_spec=eval_spec)

  return
