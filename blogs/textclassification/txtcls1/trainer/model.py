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

tf.logging.set_verbosity(tf.logging.INFO)

# variables set by init()
BUCKET = None
NUM_EPOCHS = 100
WORD_VOCAB_FILE = None 
N_WORDS = -1 # set by init

# describe your data
TARGETS = ['nytimes', 'github', 'techcrunch']
MAX_DOCUMENT_LENGTH = 20
CSV_COLUMNS = ['source', 'title']
LABEL_COLUMN = 'source'
DEFAULTS = [['null'], ['null']]

# CNN model parameters
EMBEDDING_SIZE = 10
N_FILTERS = 8
WINDOW_SIZE = 1
FILTER_SHAPE1 = [WINDOW_SIZE, EMBEDDING_SIZE]
FILTER_SHAPE2 = [WINDOW_SIZE, N_FILTERS]
POOLING_WINDOW = 4
POOLING_STRIDE = 2


def init(bucket, num_epochs):
  global BUCKET, NUM_EPOCHS, WORD_VOCAB_FILE, N_WORDS
  BUCKET = bucket
  NUM_EPOCHS = num_epochs
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
    for word, index in vocab_processor.vocabulary_._mapping.iteritems():
      f.write("{}\t{}\n".format(word, index))
  
  n_words = len(vocab_processor.vocabulary_) 
  print('{} words in {} being written to {}'.format(n_words, trainfile, outfilename))
  return n_words

def read_dataset(prefix, batch_size=20):
  # use prefix to create filename
  filename = 'gs://{}/txtcls1/{}*csv*'.format(BUCKET, prefix)
  if prefix == 'train':
    mode = tf.contrib.learn.ModeKeys.TRAIN
  else:
    mode = tf.contrib.learn.ModeKeys.EVAL
   
  # the actual input function passed to TensorFlow
  def _input_fn():
    num_epochs = NUM_EPOCHS if mode == tf.contrib.learn.ModeKeys.TRAIN else 1

    # could be a path to one file or a file pattern.
    input_file_names = tf.train.match_filenames_once(filename)
    filename_queue = tf.train.string_input_producer(
        input_file_names, num_epochs=num_epochs, shuffle=True)
 
    # read CSV
    reader = tf.TextLineReader()
    _, value = reader.read_up_to(filename_queue, num_records=batch_size)
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


def cnn_model(features, target, mode):
  """2 layer ConvNet to predict from sequence of words to a class."""     

  # make input features numeric
  from tensorflow.contrib import lookup
  table = lookup.index_table_from_file(
        vocabulary_file=WORD_VOCAB_FILE, num_oov_buckets=1, vocab_size=N_WORDS, default_value=-1, name="word_to_index")
  word_indexes = table.lookup(features['title'])
  word_vectors = tf.contrib.layers.embed_sequence(
      word_indexes, vocab_size=(N_WORDS+1), embed_dim=EMBEDDING_SIZE, scope='words')
  word_vectors = tf.expand_dims(word_vectors, 3)   # (1, embedding_size, 1)
 
  n_classes = len(TARGETS)
  #target = tf.one_hot(target, n_classes, 1, 0)
  #target = tf.squeeze(target, squeeze_dims=[1])

  with tf.variable_scope('CNN_Layer1'):
    # Apply Convolution filtering on input sequence.
    conv1 = tf.contrib.layers.convolution2d(
        word_vectors, N_FILTERS, FILTER_SHAPE1, padding='VALID')
    # Add a RELU for non linearity.
    conv1 = tf.nn.relu(conv1)
    # Max pooling across output of Convolution+Relu.
    pool1 = tf.nn.max_pool(
        conv1,
        ksize=[1, POOLING_WINDOW, 1, 1],
        strides=[1, POOLING_STRIDE, 1, 1],
        padding='SAME')
    # Transpose matrix so that n_filters from convolution becomes width.
    pool1 = tf.transpose(pool1, [0, 1, 3, 2])
  with tf.variable_scope('CNN_Layer2'):
    # Second level of convolution filtering.
    conv2 = tf.contrib.layers.convolution2d(
        pool1, N_FILTERS, FILTER_SHAPE2, padding='VALID')
    # Max across each filter to get useful features for classification.
    pool2 = tf.squeeze(tf.reduce_max(conv2, 1), squeeze_dims=[1])

  # Apply regular WX + B and classification.
  logits = tf.contrib.layers.fully_connected(pool2, n_classes, activation_fn=None)
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

def linear_model(features, target, mode):
  # make input features numeric
  from tensorflow.contrib import lookup
  table = lookup.index_table_from_file(
        vocabulary_file=WORD_VOCAB_FILE, num_oov_buckets=1, vocab_size=N_WORDS, default_value=-1, name="word_to_index")
  titles = tf.squeeze(features['title'], [1])
  words = tf.string_split(titles)
  words = tf.sparse_tensor_to_dense(words, default_value='ZYXW')
  words = table.lookup(words)
  print('lookup_words={}'.format(words))

  # each row has variable length of words
  # take the first MAX_DOCUMENT_LENGTH words (pad shorter titles to this)
  padding = tf.stack([tf.zeros_like(titles,dtype=tf.int64),tf.ones_like(titles,dtype=tf.int64)*MAX_DOCUMENT_LENGTH])
  words = tf.pad(words, padding)
  words = tf.slice(words, [0,0], [-1,MAX_DOCUMENT_LENGTH])
  print('words_sliced={}'.format(words))  # (?, 20)

  # embed the words in a common way
  words = tf.contrib.layers.embed_sequence(
      words, vocab_size=(N_WORDS+1), embed_dim=EMBEDDING_SIZE, scope='words')
  print('words_embed={}'.format(words)) # (?, 20, 10)

  # now do convolution
  conv = tf.contrib.layers.convolution2d(
           words, 5, [3, EMBEDDING_SIZE] , padding='VALID')
  conv = tf.nn.relu(conv1)
  words = tf.nn.max_pool(conv,
        ksize=[1, POOLING_WINDOW, 1, 1],
        strides=[1, POOLING_STRIDE, 1, 1],
        padding='SAME')
  print('words_conv={}'.format(words)) # 

  n_classes = len(TARGETS)

  logits = tf.contrib.layers.fully_connected(words, n_classes, activation_fn=None)
  print('logits={}'.format(logits))
  logits = tf.squeeze(logits, squeeze_dims=[1]) # from (?,1,3) to (?,3)
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
        tflearn.Estimator(model_fn=linear_model, model_dir=output_dir),
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
        )]
    )

