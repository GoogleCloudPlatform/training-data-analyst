import argparse

from . import model


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--train_data_path",
        help="GCS or local path to training data",
        required=True
    )
    parser.add_argument(
        "--train_epochs",
        help="Steps to run the training job for (default: 5)",
        type=int,
        default=10
    )
    parser.add_argument(
        "--eval_data_path",
        help="GCS or local path to evaluation data",
        required=True
    )
    parser.add_argument(
        "--output_dir",
        help="GCS location to write checkpoints and export models",
        required=True
    )
    parser.add_argument(
        "--log_dir",
        help="GCS location to write Tensorboard logs",
        required=True
    )
    parser.add_argument(
        "--job-dir",
        help="This is not used by our model, but it is required by gcloud",
    )
    hparams = parser.parse_args().__dict__

    model.train_and_evaluate(hparams)
