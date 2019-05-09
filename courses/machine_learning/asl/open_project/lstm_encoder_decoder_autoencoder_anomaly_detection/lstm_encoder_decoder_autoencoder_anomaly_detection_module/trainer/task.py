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
        "--sequence_length",
        help = "Number of timesteps to include in each example",
        type = int,
        default = 32
    )
    parser.add_argument(
        "--horizon",
        help = "Number of timesteps to skip into the future",
        type = int,
        default = 0
    )
    parser.add_argument(
        "--reverse_labels_sequence",
        help = "Whether we should reverse the labels sequence dimension or not",
        type = bool,
        default = True
    )
    
    # Architecture hyperparameters
    
    # LSTM hyperparameters
    parser.add_argument(
        "--shared_encoder_decoder_weights",
        help = "Whether the weights are shared between the encoder and decoder or not",
        type = bool,
        default = False
    )
    parser.add_argument(
        "--encoder_lstm_hidden_units",
        help = "Hidden layer sizes to use for LSTM encoder",
        default = "64 32 16"
    )
    parser.add_argument(
        "--decoder_lstm_hidden_units",
        help = "Hidden layer sizes to use for LSTM decoder",
        default = "16 32 64"
    )
    parser.add_argument(
        "--lstm_dropout_output_keep_probs",
        help = "Keep probabilties for LSTM outputs",
        default = "1.0 1.0 1.0"
    )

    # DNN hyperparameters
    parser.add_argument(
        "--dnn_hidden_units",
        help = "Hidden layer sizes to use for DNN",
        default = "1024 256 64"
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
        "--number_of_batch_time_anomaly_thresholds",
        help = "Number of anomaly thresholds to evaluate in the time dimension",
        type = int,
        default = 120
    )
    parser.add_argument(
        "--number_of_batch_features_anomaly_thresholds",
        help = "Number of anomaly thresholds to evaluate in the features dimension",
        type = int,
        default = 120
    )
    parser.add_argument(
        "--min_batch_time_anomaly_threshold",
        help = "The minimum anomaly threshold to evaluate in the time dimension",
        type = float,
        default = 100.0
    )
    parser.add_argument(
        "--max_batch_time_anomaly_threshold",
        help = "The maximum anomaly threshold to evaluate in the time dimension",
        type = float,
        default = 2000.0
    )
    parser.add_argument(
        "--min_batch_features_anomaly_threshold",
        help = "The minimum anomaly threshold to evaluate in the time dimension",
        type = float,
        default = 100.0
    )
    parser.add_argument(
        "--max_batch_features_anomaly_threshold",
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
    
    # Fix list arguments
    arguments["encoder_lstm_hidden_units"] = [int(x) for x in arguments["encoder_lstm_hidden_units"].split(' ')]
    arguments["decoder_lstm_hidden_units"] = [int(x) for x in arguments["decoder_lstm_hidden_units"].split(' ')]
    arguments["lstm_dropout_output_keep_probs"] = [float(x) for x in arguments["lstm_dropout_output_keep_probs"].split(' ')]
    arguments["dnn_hidden_units"] = [int(x) for x in arguments["dnn_hidden_units"].split(' ')]
    
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
