import argparse
import json
import os
import shutil

from .model import train_and_evaluate


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  # File arguments
  parser.add_argument(
      "--train_file_pattern",
      help="GCS location to read training data.",
      required=True
  )
  parser.add_argument(
      "--eval_file_pattern",
      help="GCS location to read evaluation data.",
      required=True
  )
  parser.add_argument(
      "--output_dir",
      help="GCS location to write checkpoints and export models.",
      required=True
  )
  parser.add_argument(
      "--job-dir",
      help="This model ignores this field, but it is required by gcloud.",
      default="junk"
  )

  # Sequence shape hyperparameters
  parser.add_argument(
      "--seq_len",
      help="Number of timesteps to include in each example.",
      type=int,
      default=30
  )

  # Training parameters
  parser.add_argument(
      "--train_batch_size",
      help="Number of examples in training batch.",
      type=int,
      default=32
  )
  parser.add_argument(
      "--eval_batch_size",
      help="Number of examples in evaluation batch.",
      type=int,
      default=32
  )
  parser.add_argument(
      "--train_steps",
      help="Number of batches to train.",
      type=int,
      default=1024
  )
  parser.add_argument(
      "--learning_rate",
      help="How quickly or slowly we train our model by scaling the gradient.",
      type=float,
      default=0.1
  )
  parser.add_argument(
      "--start_delay_secs",
      help="Number of seconds to wait before first evaluation.",
      type=int,
      default=60
  )
  parser.add_argument(
      "--throttle_secs",
      help="Number of seconds to wait between evaluations.",
      type=int,
      default=120
  )

  ## LSTM hyperparameters
  parser.add_argument(
      "--lstm_hidden_units",
      help="Hidden layer sizes to use for LSTM.",
      type=str,
      default="64,32,16"
  )

  # Parse all arguments
  args = parser.parse_args()
  arguments = args.__dict__

  # Unused args provided by service
  arguments.pop("job_dir", None)
  arguments.pop("job-dir", None)
  
  # Fix list arguments
  arguments["lstm_hidden_units"] = [
      int(x) for x in arguments["lstm_hidden_units"].split(",")]

  # Append trial_id to path if we are doing hptuning
  # This code can be removed if you are not using hyperparameter tuning
  arguments["output_dir"] = os.path.join(
      arguments["output_dir"],
      json.loads(
          os.environ.get("TF_CONFIG", "{}")
          ).get("task", {}).get("trial", "")
      )

  # Run the model
  shutil.rmtree(path=arguments["output_dir"], ignore_errors=True) # start fresh each time
  train_and_evaluate(arguments)
