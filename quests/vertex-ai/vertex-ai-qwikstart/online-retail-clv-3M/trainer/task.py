import os
import argparse

from trainer import model

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # Vertex custom container training args. These are set by Vertex AI during training can be overwritten.
    parser.add_argument('--model-dir', dest='model-dir',
                        default=os.environ['AIP_MODEL_DIR'], type=str, help='Model dir.')
    parser.add_argument('--checkpoint-dir', dest='checkpoint-dir',
                        default=os.environ['AIP_CHECKPOINT_DIR'], type=str, help='Checkpoint dir set during Vertex AI training.')    
    parser.add_argument('--tensorboard-dir', dest='tensorboard-dir',
                        default=os.environ['AIP_TENSORBOARD_LOG_DIR'], type=str, help='Tensorboard dir set during Vertex AI training.')    
    parser.add_argument('--data-format', dest='data-format',
                        default=os.environ['AIP_DATA_FORMAT'], type=str, help="Tabular data format set during Vertex AI training. E.g.'csv', 'bigquery'")
    parser.add_argument('--training-data-uri', dest='training-data-uri',
                        default=os.environ['AIP_TRAINING_DATA_URI'], type=str, help='Training data GCS or BQ URI set during Vertex AI training.')
    parser.add_argument('--validation-data-uri', dest='validation-data-uri',
                        default=os.environ['AIP_VALIDATION_DATA_URI'], type=str, help='Validation data GCS or BQ URI set during Vertex AI training.')
    parser.add_argument('--test-data-uri', dest='test-data-uri',
                        default=os.environ['AIP_TEST_DATA_URI'], type=str, help='Test data GCS or BQ URI set during Vertex AI training.')
    # Model training args.
    parser.add_argument('--learning-rate', dest='learning-rate', default=0.001, type=float, help='Learning rate for optimizer.')
    parser.add_argument('--dropout', dest='dropout', default=0.2, type=float, help='Float percentage of DNN nodes [0,1] to drop for regularization.')    
    parser.add_argument('--batch-size', dest='batch-size', default=16, type=int, help='Number of examples during each training iteration.')    
    parser.add_argument('--n-train-examples', dest='n-train-examples', default=2638, type=int, help='Number of examples to train on.')
    parser.add_argument('--stop-point', dest='stop-point', default=10, type=int, help='Number of passes through the dataset during training to achieve convergence.')
    parser.add_argument('--n-checkpoints', dest='n-checkpoints', default=10, type=int, help='Number of model checkpoints to save during training.')
    
    args = parser.parse_args()
    hparams = args.__dict__

    model.train_evaluate_explain_model(hparams)
