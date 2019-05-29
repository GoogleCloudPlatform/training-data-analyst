import argparse
import json
import os

from . import model

import tensorflow as tf

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  # File arguments
  parser.add_argument(
    "--train_file_pattern",
    help = "GCS location to read training data",
    required = True
  )
  parser.add_argument(
    "--eval_file_pattern",
    help = "GCS location to read evaluation data",
    required = True
  )
  parser.add_argument(
    "--output_dir",
    help = "GCS location to write checkpoints and export models",
    required = True
  )
  parser.add_argument(
    "--job-dir",
    help = "this model ignores this field, but it is required by gcloud",
    default = "junk"
  )
  
  # Sequence shape hyperparameters
  parser.add_argument(
    "--seq_len",
    help = "Number of timesteps to include in each example",
    type = int,
    default = 32
  )
  
  # Training parameters
  parser.add_argument(
    "--train_batch_size",
    help = "Number of examples in training batch",
    type = int,
    default = 32
  )
  parser.add_argument(
    "--eval_batch_size",
    help = "Number of examples in evaluation batch",
    type = int,
    default = 32
  )
  parser.add_argument(
    "--train_steps",
    help = "Number of batches to train for",
    type = int,
    default = 2000
  )
  parser.add_argument(
    "--learning_rate",
    help = "The learning rate, how quickly or slowly we train our model by scaling the gradient",
    type = float,
    default = 0.1
  )
  parser.add_argument(
    "--start_delay_secs",
    help = "Number of seconds to wait before first evaluation",
    type = int,
    default = 60
  )
  parser.add_argument(
    "--throttle_secs",
    help = "Number of seconds to wait between evaluations",
    type = int,
    default = 120
  )
  
  # Anomaly detection
  parser.add_argument(
    "--evaluation_mode",
    help = "Which evaluation mode we are in (reconstruction, calculate_error_distribution_statistics, tune_anomaly_thresholds)",
    type = str,
    default = "reconstruction"
  )
  parser.add_argument(
    "--k_principal_components",
    help = "The top k principal components to keep after eigendecomposition",
    type = int,
    default = 3
  )
  parser.add_argument(
    "--num_time_anomaly_thresholds",
    help = "Number of anomaly thresholds to evaluate in the time dimension",
    type = int,
    default = 120
  )
  parser.add_argument(
    "--num_features_anomaly_thresholds",
    help = "Number of anomaly thresholds to evaluate in the features dimension",
    type = int,
    default = 120
  )
  parser.add_argument(
    "--min_time_anomaly_threshold",
    help = "The minimum anomaly threshold to evaluate in the time dimension",
    type = float,
    default = 100.0
  )
  parser.add_argument(
    "--max_time_anomaly_threshold",
    help = "The maximum anomaly threshold to evaluate in the time dimension",
    type = float,
    default = 2000.0
  )
  parser.add_argument(
    "--min_features_anomaly_threshold",
    help = "The minimum anomaly threshold to evaluate in the time dimension",
    type = float,
    default = 100.0
  )
  parser.add_argument(
    "--max_features_anomaly_threshold",
    help = "The maximum anomaly threshold to evaluate in the time dimension",
    type = float,
    default = 2000.0
  )
  parser.add_argument(
    "--time_anomaly_threshold",
    help = "The anomaly threshold in the time dimension",
    type = float,
    default = None
  )
  parser.add_argument(
    "--features_anomaly_threshold",
    help = "The anomaly threshold in the features dimension",
    type = float,
    default = None
  )
  parser.add_argument(
    "--eps",
    help = "The precision value to add to the covariance matrix before inversion to avoid being singular",
    type = str,
    default = "1e-12"
  )
  parser.add_argument(
    "--f_score_beta",
    help = "The value of beta of the f-beta score",
    type = float,
    default = 0.05
  )
  
  # Parse all arguments
  args = parser.parse_args()
  arguments = args.__dict__

  # Unused args provided by service
  arguments.pop("job_dir", None)
  arguments.pop("job-dir", None)
  
  # Fix eps argument
  arguments["eps"] = float(arguments["eps"])

  # Append trial_id to path if we are doing hptuning
  # This code can be removed if you are not using hyperparameter tuning
  arguments["output_dir"] = os.path.join(
    arguments["output_dir"],
    json.loads(
      os.environ.get("TF_CONFIG", "{}")
    ).get("task", {}).get("trial", "")
  )

  # Run the training job
  model.train_and_evaluate(arguments)
