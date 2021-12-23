
import os
import argparse

from trainer import model

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    # Vertex custom container training args. These are set by Vertex AI during training but can also be overwritten.
    parser.add_argument('--model-dir', dest='model-dir',
                        default=os.environ['AIP_MODEL_DIR'], type=str, help='GCS URI for saving model artifacts.')

    # Model training args.
    parser.add_argument('--tfhub-bert-preprocessor', dest='tfhub-bert-preprocessor', 
                        default='https://tfhub.dev/tensorflow/bert_en_uncased_preprocess/3', type=str, help='TF-Hub URL.')
    parser.add_argument('--tfhub-bert-encoder', dest='tfhub-bert-encoder', 
                        default='https://tfhub.dev/tensorflow/small_bert/bert_en_uncased_L-2_H-128_A-2/2', type=str, help='TF-Hub URL.')     
    parser.add_argument('--initial-learning-rate', dest='initial-learning-rate', default=3e-5, type=float, help='Learning rate for optimizer.')
    parser.add_argument('--epochs', dest='epochs', default=3, type=int, help='Training iterations.')    
    parser.add_argument('--batch-size', dest='batch-size', default=32, type=int, help='Number of examples during each training iteration.')    
    parser.add_argument('--dropout', dest='dropout', default=0.1, type=float, help='Float percentage of DNN nodes [0,1] to drop for regularization.')    
    parser.add_argument('--seed', dest='seed', default=42, type=int, help='Random number generator seed to prevent overlap between train and val sets.')
    
    args = parser.parse_args()
    hparams = args.__dict__

    model.train_evaluate(hparams)
