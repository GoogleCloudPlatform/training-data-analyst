#!/usr/bin/env python

# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import shutil
import tensorflow as tf
import tensorflow.contrib.learn as tflearn
import tensorflow.contrib.layers as tflayers
from tensorflow.contrib.learn.python.learn import learn_runner
import tensorflow.contrib.metrics as metrics
from tensorflow.python.platform import gfile
from tensorflow.contrib import lookup

tf.logging.set_verbosity(tf.logging.INFO)

# variables set by init()
BUCKET = None
TRAIN_STEPS = 1000
WORD_VOCAB_FILE = None 
N_WORDS = -1

# hardcoded into graph
BATCH_SIZE = 32

# describe your data
TARGETS = ['nytimes', 'github', 'techcrunch']
MAX_DOCUMENT_LENGTH = 20
CSV_COLUMNS = ['source', 'title']
LABEL_COLUMN = 'source'
DEFAULTS = [['null'], ['null']]
PADWORD = 'ZYXW'

def init(bucket, num_steps):
  global BUCKET, TRAIN_STEPS, WORD_VOCAB_FILE, N_WORDS
  BUCKET = bucket
  TRAIN_STEPS = num_steps
  WORD_VOCAB_FILE = 'gs://{}/txtcls1/vocab_words'.format(BUCKET)
  N_WORDS = save_vocab('gs://{}/txtcls1/train.csv'.format(BUCKET), 'title', WORD_VOCAB_FILE);

def save_vocab(trainfile, txtcolname, outfilename):
  if trainfile.startswith('gs://'):
    import subprocess
    tmpfile = "vocab.csv"
    subprocess.check_call("gsutil cp {} {}".format(trainfile, tmpfile).split(" "))
    filename = tmpfile
  else:
    filename = trainfile
  import pandas as pd
  df = pd.read_csv(filename, header=None, sep='\t', names=['source', 'title'])
  # the text to be classified
  vocab_processor = tflearn.preprocessing.VocabularyProcessor(MAX_DOCUMENT_LENGTH, min_frequency=10)
  vocab_processor.fit(df[txtcolname])

  with gfile.Open(outfilename, 'wb') as f:
    f.write("{}\n".format(PADWORD))
    for word, index in vocab_processor.vocabulary_._mapping.iteritems():
      f.write("{}\n".format(word))
  nwords = len(vocab_processor.vocabulary_)
  print('{} words into {}'.format(nwords, outfilename))
  return nwords + 2  # PADWORD and <UNK>

def read_dataset(prefix):
  # use prefix to create filename
  filename = 'gs://{}/txtcls1/{}*csv*'.format(BUCKET, prefix)
  if prefix == 'train':
    mode = tf.contrib.learn.ModeKeys.TRAIN
  else:
    mode = tf.contrib.learn.ModeKeys.EVAL
   
  # the actual input function passed to TensorFlow
  def _input_fn():
    # could be a path to one file or a file pattern.
    input_file_names = tf.train.match_filenames_once(filename)
    filename_queue = tf.train.string_input_producer(input_file_names, shuffle=True)
 
    # read CSV
    reader = tf.TextLineReader()
    _, value = reader.read_up_to(filename_queue, num_records=BATCH_SIZE)
    #value = tf.train.shuffle_batch([value], BATCH_SIZE, capacity=10*BATCH_SIZE, min_after_dequeue=BATCH_SIZE, enqueue_many=True, allow_smaller_final_batch=False)
    value_column = tf.expand_dims(value, -1)
    columns = tf.decode_csv(value_column, record_defaults=DEFAULTS, field_delim='\t')
    features = dict(zip(CSV_COLUMNS, columns))
    label = features.pop(LABEL_COLUMN)

    # make targets numeric
    table = tf.contrib.lookup.index_table_from_tensor(
                   mapping=tf.constant(TARGETS), num_oov_buckets=0, default_value=-1)
    target = table.lookup(label)

    return features, target
  
  return _input_fn

# CNN model parameters
EMBEDDING_SIZE = 10
WINDOW_SIZE = EMBEDDING_SIZE
STRIDE = int(WINDOW_SIZE/2)
def cnn_model(features, target, mode):
    table = lookup.index_table_from_file(vocabulary_file=WORD_VOCAB_FILE, num_oov_buckets=1, default_value=-1)
    
    # string operations
    titles = tf.squeeze(features['title'], [1])
    words = tf.string_split(titles)
    densewords = tf.sparse_tensor_to_dense(words, default_value=PADWORD)
    numbers = table.lookup(densewords)
    padding = tf.constant([[0,0],[0,MAX_DOCUMENT_LENGTH]])
    padded = tf.pad(numbers, padding)
    sliced = tf.slice(padded, [0,0], [-1, MAX_DOCUMENT_LENGTH])
    print('words_sliced={}'.format(words))  # (?, 20)

    # layer to take the words and convert them into vectors (embeddings)
    embeds = tf.contrib.layers.embed_sequence(sliced, vocab_size=N_WORDS, embed_dim=EMBEDDING_SIZE)
    print('words_embed={}'.format(embeds)) # (?, 20, 10)
    
    # now do convolution
    conv = tf.contrib.layers.conv2d(embeds, 1, WINDOW_SIZE, stride=STRIDE, padding='SAME') # (?, 4, 1)
    conv = tf.nn.relu(conv) # (?, 4, 1)
    words = tf.squeeze(conv, [2]) # (?, 4)
    print('words_conv={}'.format(words)) # (?, 4)

    n_classes = len(TARGETS)

    logits = tf.contrib.layers.fully_connected(words, n_classes, activation_fn=None)
    #print('logits={}'.format(logits)) # (?, 3)
    predictions_dict = {
      'source': tf.gather(TARGETS, tf.argmax(logits, 1)),
      'class': tf.argmax(logits, 1),
      'prob': tf.nn.softmax(logits)
    }

    if mode == tf.contrib.learn.ModeKeys.TRAIN or mode == tf.contrib.learn.ModeKeys.EVAL:
       loss = tf.losses.sparse_softmax_cross_entropy(target, logits)
       train_op = tf.contrib.layers.optimize_loss(
         loss,
         tf.contrib.framework.get_global_step(),
         optimizer='Adam',
         learning_rate=0.01)
    else:
       loss = None
       train_op = None

    return tflearn.ModelFnOps(
      mode=mode,
      predictions=predictions_dict,
      loss=loss,
      train_op=train_op)


def serving_input_fn():
    feature_placeholders = {
      'title': tf.placeholder(tf.string, [None]),
    }
    features = {
      key: tf.expand_dims(tensor, -1)
      for key, tensor in feature_placeholders.items()
    }
    return tflearn.utils.input_fn_utils.InputFnOps(
      features,
      None,
      feature_placeholders)

def get_train():
  return read_dataset('train')

def get_valid():
  return read_dataset('eval')

from tensorflow.contrib.learn.python.learn.utils import saved_model_export_utils
def experiment_fn(output_dir):
    # run experiment
    return tflearn.Experiment(
        tflearn.Estimator(model_fn=cnn_model, model_dir=output_dir),
        train_input_fn=get_train(),
        eval_input_fn=get_valid(),
        eval_metrics={
            'acc': tflearn.MetricSpec(
                metric_fn=metrics.streaming_accuracy, prediction_key='class'
            )
        },
        export_strategies=[saved_model_export_utils.make_export_strategy(
            serving_input_fn,
            default_output_alternative_key=None,
            exports_to_keep=1
        )],
        train_steps = TRAIN_STEPS
    )

