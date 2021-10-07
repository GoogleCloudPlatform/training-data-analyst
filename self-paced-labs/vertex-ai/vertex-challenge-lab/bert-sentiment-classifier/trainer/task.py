
import os
import argparse

from trainer import model

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # Vertex custom container training args. These are set by Vertex AI during training but can also be overwritten.
    parser.add_argument('--model-dir', dest='model-dir',
                        default=os.environ['AIP_MODEL_DIR'], type=str, help='GCS URI for saving model artifacts.')
    parser.add_argument('--data-dir', dest='data-dir',
                        default='gs://dougkelly-vertex-demos-vertex-challenge-lab/data', type=str, help='GCS URI for saving dataset.')    
    parser.add_argument('--tf-hub-bert-preprocessor', dest='tf-hub-bert-preprocessor', 
                        default='https://tfhub.dev/tensorflow/bert_en_uncased_preprocess/3', type=str, help='TF-Hub URL.')
    parser.add_argument('--tf-hub-bert-encoder', dest='tf-hub-bert-encoder', 
                        default='https://tfhub.dev/tensorflow/small_bert/bert_en_uncased_L-2_H-128_A-2/2', type=str, help='TF-Hub URL.')     

    # Model training args.
    parser.add_argument('--initial-learning-rate', dest='initial-learning-rate', default=3e-5, type=float, help='Learning rate for optimizer.')
    parser.add_argument('--batch-size', dest='batch-size', default=32, type=int, help='Number of examples during each training iteration.')    
    parser.add_argument('--dropout', dest='dropout', default=0.1, type=float, help='Float percentage of DNN nodes [0,1] to drop for regularization.')    

    
    args = parser.parse_args()
    hparams = args.__dict__

    model.train_evaluate(hparams)
