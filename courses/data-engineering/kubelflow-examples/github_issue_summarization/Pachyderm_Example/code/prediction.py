import argparse
import keras
import pandas as pd
from seq2seq_utils import load_text_processor
from seq2seq_utils import Seq2Seq_Inference

# Parsing flags.
parser = argparse.ArgumentParser()
parser.add_argument("--input_model_h5")
parser.add_argument("--input_body_preprocessor_dpkl")
parser.add_argument("--input_title_preprocessor_dpkl")
parser.add_argument("--input_testdf_csv")
parser.add_argument("--input_prediction_count", type=int, default=50)
args = parser.parse_args()
print(args)

# Read data.
testdf = pd.read_csv(args.input_testdf_csv)

# Load model, preprocessors.
seq2seq_Model = keras.models.load_model(args.input_model_h5)
num_encoder_tokens, body_pp = load_text_processor(args.input_body_preprocessor_dpkl)
num_decoder_tokens, title_pp = load_text_processor(args.input_title_preprocessor_dpkl)

# Prepare inference.
seq2seq_inf = Seq2Seq_Inference(encoder_preprocessor=body_pp,
                                 decoder_preprocessor=title_pp,
                                 seq2seq_model=seq2seq_Model)

# Output predictions for n random rows in the test set.
seq2seq_inf.demo_model_predictions(n=args.input_prediction_count, issue_df=testdf)
