import argparse
import dill as dpickle
import numpy as np
from ktext.preprocess import processor
import pandas as pd

# Parsing flags.
parser = argparse.ArgumentParser()
parser.add_argument("--input_traindf_csv")
parser.add_argument("--output_body_preprocessor_dpkl")
parser.add_argument("--output_title_preprocessor_dpkl")
parser.add_argument("--output_train_title_vecs_npy")
parser.add_argument("--output_train_body_vecs_npy")
args = parser.parse_args()
print(args)

# Read data.
traindf = pd.read_csv(args.input_traindf_csv)
train_body_raw = traindf.body.tolist()
train_title_raw = traindf.issue_title.tolist()

# Clean, tokenize, and apply padding / truncating such that each document
# length = 70. Also, retain only the top 8,000 words in the vocabulary and set
# the remaining words to 1 which will become common index for rare words.
body_pp = processor(keep_n=8000, padding_maxlen=70)
train_body_vecs = body_pp.fit_transform(train_body_raw)

print('Example original body:', train_body_raw[0])
print('Example body after pre-processing:', train_body_vecs[0])

# Instantiate a text processor for the titles, with some different parameters.
title_pp = processor(append_indicators=True, keep_n=4500,
                     padding_maxlen=12, padding='post')

# process the title data
train_title_vecs = title_pp.fit_transform(train_title_raw)

print('Example original title:', train_title_raw[0])
print('Example title after pre-processing:', train_title_vecs[0])

# Save the preprocessor.
with open(args.output_body_preprocessor_dpkl, 'wb') as f:
  dpickle.dump(body_pp, f, protocol=2)

with open(args.output_title_preprocessor_dpkl, 'wb') as f:
  dpickle.dump(title_pp, f, protocol=2)

# Save the processed data.
np.save(args.output_train_title_vecs_npy, train_title_vecs)
np.save(args.output_train_body_vecs_npy, train_body_vecs)
