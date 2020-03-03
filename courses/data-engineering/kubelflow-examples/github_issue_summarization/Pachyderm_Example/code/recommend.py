import argparse
import keras
import pandas as pd
from seq2seq_utils import load_text_processor
from seq2seq_utils import Seq2Seq_Inference

# Parsing flags.
parser = argparse.ArgumentParser()
parser.add_argument("--input_csv")
parser.add_argument("--input_model_h5")
parser.add_argument("--input_body_preprocessor_dpkl")
parser.add_argument("--input_title_preprocessor_dpkl")
parser.add_argument("--input_testdf_csv")
parser.add_argument("--input_topic_number", type=int, default=1)
args = parser.parse_args()
print(args)

# Read data.
all_data_df = pd.read_csv(args.input_csv)
testdf = pd.read_csv(args.input_testdf_csv)

# Load model, preprocessors.
num_encoder_tokens, body_pp = load_text_processor(args.input_body_preprocessor_dpkl)
num_decoder_tokens, title_pp = load_text_processor(args.input_title_preprocessor_dpkl)
seq2seq_Model = keras.models.load_model(args.input_model_h5)

# Prepare the recommender.
all_data_bodies = all_data_df['body'].tolist()
all_data_vectorized = body_pp.transform_parallel(all_data_bodies)
seq2seq_inf_rec = Seq2Seq_Inference(encoder_preprocessor=body_pp,
                                    decoder_preprocessor=title_pp,
                                    seq2seq_model=seq2seq_Model)
recsys_annoyobj = seq2seq_inf_rec.prepare_recommender(all_data_vectorized, all_data_df)

# Output recommendations for n topics.
seq2seq_inf_rec.demo_model_predictions(n=args.input_topic_number, issue_df=testdf, threshold=1)
