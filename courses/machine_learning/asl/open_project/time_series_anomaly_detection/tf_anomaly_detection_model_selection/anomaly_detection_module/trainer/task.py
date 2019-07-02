import argparse
import json
import os

from model import train_and_evaluate


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
      default=32
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
      default=2000
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

  # Model hyperparameters
  # dense_autoencoder, lstm_enc_dec_autoencoder, pca
  parser.add_argument(
      "--model_type",
      help="Which model type we will use.",
      type=str,
      default="dense_autoencoder"
  )
  ## Dense Autoencoder
  parser.add_argument(
      "--enc_dnn_hidden_units",
      help="Hidden layer sizes to use for encoder DNN.",
      default="1024 256 64"
  )
  parser.add_argument(
      "--latent_vector_size",
      help="Number of neurons for latent vector between encoder and decoder.",
      type=int,
      default=8
  )
  parser.add_argument(
      "--dec_dnn_hidden_units",
      help="Hidden layer sizes to use for decoder DNN.",
      default="64 256 1024"
  )
  parser.add_argument(
      "--time_loss_weight",
      help="Amount to weight the time based loss.",
      type=float,
      default=1.0
  )
  parser.add_argument(
      "--feat_loss_weight",
      help="Amount to weight the features based loss.",
      type=float,
      default=1.0
  )
  ## LSTM Encoder-Decoder Autoencoder
  parser.add_argument(
      "--reverse_labels_sequence",
      help="Whether we should reverse the labels sequence dimension or not.",
      type=bool,
      default=True
  )
  parser.add_argument(
      "--enc_lstm_hidden_units",
      help="Hidden layer sizes to use for LSTM encoder.",
      default="64 32 16"
  )
  parser.add_argument(
      "--dec_lstm_hidden_units",
      help="Hidden layer sizes to use for LSTM decoder.",
      default="16 32 64"
  )
  parser.add_argument(
      "--lstm_dropout_output_keep_probs",
      help="Keep probabilties for LSTM outputs.",
      default="1.0 1.0 1.0"
  )
  parser.add_argument(
      "--dnn_hidden_units",
      help="Hidden layer sizes to use for DNN.",
      default="1024 256 64"
  )
  ## PCA
  parser.add_argument(
      "--k_principal_components",
      help="Top k principal components to keep after eigendecomposition.",
      type=int,
      default=3
  )

  # Anomaly detection
  # reconstruction, calculate_error_distribution_statistics,
  # and tune_anomaly_thresholds
  parser.add_argument(
      "--training_mode",
      help="Which training mode we are in.",
      type=str,
      default="reconstruction"
  )
  parser.add_argument(
      "--labeled_tune_thresh",
      help="If we have a labeled dataset for supervised anomaly tuning.",
      type=bool,
      default=True
  )
  parser.add_argument(
      "--num_time_anom_thresh",
      help="Number of anomaly thresholds to evaluate in time dimension.",
      type=int,
      default=120
  )
  parser.add_argument(
      "--num_feat_anom_thresh",
      help="Number of anomaly thresholds to evaluate in features dimension.",
      type=int,
      default=120
  )
  parser.add_argument(
      "--min_time_anom_thresh",
      help="Minimum anomaly threshold to evaluate in time dimension.",
      type=float,
      default=100.0
  )
  parser.add_argument(
      "--max_time_anom_thresh",
      help="Maximum anomaly threshold to evaluate in time dimension.",
      type=float,
      default=2000.0
  )
  parser.add_argument(
      "--min_feat_anom_thresh",
      help="Minimum anomaly threshold to evaluate in features dimension.",
      type=float,
      default=100.0
  )
  parser.add_argument(
      "--max_feat_anom_thresh",
      help="Maximum anomaly threshold to evaluate in features dimension.",
      type=float,
      default=2000.0
  )
  parser.add_argument(
      "--time_thresh_scl",
      help="Max num of std devs for time mahalanobis distance to be normal.",
      type=float,
      default=2.0
  )
  parser.add_argument(
      "--feat_thresh_scl",
      help="Max num of std devs for feature mahalanobis distance to be normal.",
      type=float,
      default=2.0
  )
  parser.add_argument(
      "--time_anom_thresh",
      help="Anomaly threshold in time dimension.",
      type=float,
      default=None
  )
  parser.add_argument(
      "--feat_anom_thresh",
      help="Anomaly threshold in features dimension.",
      type=float,
      default=None
  )
  parser.add_argument(
      "--eps",
      help="Added to the cov matrix before inversion to avoid being singular.",
      type=str,
      default="1e-12"
  )
  parser.add_argument(
      "--f_score_beta",
      help="Value of beta of the f-beta score.",
      type=float,
      default=0.05
  )

  # Parse all arguments
  args = parser.parse_args()
  arguments = args.__dict__

  # Unused args provided by service
  arguments.pop("job_dir", None)
  arguments.pop("job-dir", None)

  # Fix list arguments
  ## Dense Autoencoder
  arguments["enc_dnn_hidden_units"] = [
      int(x) for x in arguments["enc_dnn_hidden_units"].split(" ")]
  arguments["dec_dnn_hidden_units"] = [
      int(x) for x in arguments["dec_dnn_hidden_units"].split(" ")]

  ## LSTM Encoder-Decoder Autoencoder
  arguments["enc_lstm_hidden_units"] = [
      int(x) for x in arguments["enc_lstm_hidden_units"].split(" ")]
  arguments["dec_lstm_hidden_units"] = [
      int(x) for x in arguments["dec_lstm_hidden_units"].split(" ")]
  arguments["lstm_dropout_output_keep_probs"] = [
      float(x) for x in arguments["lstm_dropout_output_keep_probs"].split(" ")]
  arguments["dnn_hidden_units"] = [
      int(x) for x in arguments["dnn_hidden_units"].split(" ")]

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
  train_and_evaluate(arguments)
