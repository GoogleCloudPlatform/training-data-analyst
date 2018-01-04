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
import numpy as np
import tensorflow as tf
from tensorflow.contrib.learn.python.learn import learn_runner
from tensorflow.contrib.learn.python.learn import preprocessing
from tensorflow.python.lib.io import file_io
from tensorflow.python.platform import gfile
from tensorflow.contrib import lookup

tf.logging.set_verbosity(tf.logging.INFO)

# variables set by init()
WORD_VOCAB_FILE = None 
N_WORDS = -1
PRETRAINED_EMBEDDING = None

# hardcoded into graph
BATCH_SIZE = 32

# describe your data
TARGETS = ['nytimes', 'github', 'techcrunch']
MAX_DOCUMENT_LENGTH = 20
CSV_COLUMNS = ['source', 'title']
LABEL_COLUMN = 'source'
DEFAULTS = [['null'], ['null']]
PADWORD = 'ZYXW'

# Word2Vec for pretrained embedding
class Word2Vec:
  '''
  vocab, embeddings
  '''
  def vocab_size(self):
    return len(self.vocab)
  
  def embed_dim(self):
    return len(self.embeddings[0])
  
  def __init__(self, filename):
    import gzip, StringIO
    self.vocab = [PADWORD]
    self.embeddings = [0]
    with file_io.FileIO(filename, mode='rb') as f:
      compressedFile = StringIO.StringIO(f.read())
      decompressedFile = gzip.GzipFile(fileobj=compressedFile)
      for line in decompressedFile:
        pieces = line.split()
        self.vocab.append(pieces[0])
        self.embeddings.append(np.asarray(pieces[1:], dtype='float32'))
    self.embeddings[0] = np.zeros_like(self.embeddings[1])
    
    self.vocab.append('') # for out-of-value words
    self.embeddings.append(np.ones_like(self.embeddings[1]))

    self.embeddings = np.array(self.embeddings)
    print('Loaded {}D vectors for {} words from {}'.format(self.embed_dim(), self.vocab_size(), filename))
    # will be set in init(sess)
    self.table = None
    self.wordid_to_embed = None

  # this method is called from a SessionRunHook, so that it has access to the session
  def init(sess):
    # variables needed by get_embedding ...
    self.table = tf.contrib.lookup.index_table_from_tensor(
                    tf.convert_to_tensor(self.vocab[:-1]), num_oov_buckets=1)
    self.wordid_to_embed = tf.Variable(tf.constant(0.0, shape=[self.vocab_size(), self.embed_dim()]),
                                  trainable=False, name="embedding")
    embedding_placeholder = tf.placeholder(tf.float32, [self.vocab_size(), self.embed_dim()])
    embedding_init = self.wordid_to_embed.assign(embedding_placeholder)
    sess.run(embedding_init, feed_dict={embedding_placeholder: self.embeddings})
    print('Loaded pretrained embedding into tensorflow graph')

  def get_embedding(self, lines):
    words = tf.string_split(lines)
    densewords = tf.sparse_tensor_to_dense(words, default_value=PADWORD)
    numbers = self.table.lookup(densewords)
    padding = tf.constant([[0,0],[0,MAX_DOCUMENT_LENGTH]])
    padded = tf.pad(numbers, padding)
    sliced = tf.slice(padded, [0,0], [-1, MAX_DOCUMENT_LENGTH])
    embeds = tf.nn.embedding_lookup(self.wordid_to_embed, sliced)
    return embeds
    

def init(hparams):
  global WORD_VOCAB_FILE, N_WORDS, PRETRAINED_EMBEDDING
  if len(hparams['glove_embedding']) == 0:
     # no pre-trained embedding, so learn it from the dataset itself
     BUCKET = hparams['bucket']
     WORD_VOCAB_FILE = 'gs://{}/txtcls1/vocab_words'.format(BUCKET)
     N_WORDS = save_vocab('gs://{}/txtcls1/train.csv'.format(BUCKET), 'title', WORD_VOCAB_FILE);
     print('Stored training dataset vocabulary into {}'.format(WORD_VOCAB_FILE))
  else:
     # use pretrained embedding
     print('Will use pretrained embeddings from {}'.format(hparams['glove_embedding']))
     PRETRAINED_EMBEDDING = Word2Vec(hparams['glove_embedding'])
   
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
  vocab_processor = preprocessing.VocabularyProcessor(MAX_DOCUMENT_LENGTH, min_frequency=10)
  vocab_processor.fit(df[txtcolname])

  with gfile.Open(outfilename, 'wb') as f:
    f.write("{}\n".format(PADWORD))
    for word, index in vocab_processor.vocabulary_._mapping.iteritems():
      f.write("{}\n".format(word))
  nwords = len(vocab_processor.vocabulary_)
  print('{} words into {}'.format(nwords, outfilename))
  return nwords + 2  # PADWORD and <UNK>

def read_dataset(hparams, prefix, batch_size=BATCH_SIZE):
  # use prefix to create filename
  filename = 'gs://{}/txtcls1/{}*csv*'.format(hparams['bucket'], prefix)
  if prefix == 'train':
    mode = tf.estimator.ModeKeys.TRAIN
  else:
    mode = tf.estimator.ModeKeys.EVAL
   
  # the actual input function passed to TensorFlow
  def _input_fn():
    # could be a path to one file or a file pattern.
    input_file_names = tf.train.match_filenames_once(filename)
    filename_queue = tf.train.string_input_producer(input_file_names, shuffle=True)
 
    # read CSV
    reader = tf.TextLineReader()
    _, value = reader.read_up_to(filename_queue, num_records=batch_size)
    if mode == tf.estimator.ModeKeys.TRAIN:
       value = tf.train.shuffle_batch([value], batch_size, capacity=10*batch_size, min_after_dequeue=batch_size, enqueue_many=True, allow_smaller_final_batch=False)
    value_column = tf.expand_dims(value, -1)
    columns = tf.decode_csv(value_column, record_defaults=DEFAULTS, field_delim='\t')
    features = dict(zip(CSV_COLUMNS, columns))
    label = features.pop(LABEL_COLUMN)

    # make labels numeric
    table = tf.contrib.lookup.index_table_from_tensor(
                   mapping=tf.constant(TARGETS), num_oov_buckets=0, default_value=-1)
    labels = table.lookup(label)

    return features, labels
  
  return _input_fn

# embedding parameters
def get_embedding(hparams, titles, embed_size):
    table = lookup.index_table_from_file(vocabulary_file=WORD_VOCAB_FILE, num_oov_buckets=1, default_value=-1)
    
    # string operations
    words = tf.string_split(titles)
    densewords = tf.sparse_tensor_to_dense(words, default_value=PADWORD)
    numbers = table.lookup(densewords)
    padding = tf.constant([[0,0],[0,MAX_DOCUMENT_LENGTH]])
    padded = tf.pad(numbers, padding)
    sliced = tf.slice(padded, [0,0], [-1, MAX_DOCUMENT_LENGTH])
    #print('words_sliced={}'.format(words))  # (?, 20)

    # layer to take the words and convert them into vectors (embeddings)
    embeds = tf.contrib.layers.embed_sequence(sliced, vocab_size=N_WORDS, embed_dim=embed_size)
    #print('words_embed={}'.format(embeds)) # (?, 20, 10)
    return embeds

# CNN model parameters
def cnn_model(features, labels, mode, params):
    # the only input column we care about is 'title'
    titles = tf.squeeze(features['title'], [1])
    if len(params['glove_embedding']) == 0:
       EMBEDDING_SIZE = 10
       embeds = get_embedding(params, titles, EMBEDDING_SIZE) # (?, MAX_DOCUMENT_LENGTH, EMBEDDING_SIZE)
    else:
       embeds = PRETRAINED_EMBEDDING.get_embedding(titles)
       EMBEDDING_SIZE = PRETRAINED_EMBEDDING.embed_dim()
    
    # now do convolution
    WINDOW_SIZE = EMBEDDING_SIZE
    STRIDE = int(WINDOW_SIZE/2)
    conv = tf.contrib.layers.conv2d(embeds, 1, WINDOW_SIZE, stride=STRIDE, padding='SAME') # (?, 4, 1)
    conv = tf.nn.relu(conv) # (?, 4, 1)
    words = tf.squeeze(conv, [2]) # (?, 4)
    #print('words_conv={}'.format(words)) # (?, 4)

    n_classes = len(TARGETS)

    logits = tf.layers.dense(words, n_classes, activation=None)
    #print('logits={}'.format(logits)) # (?, 3)
    predictions_dict = {
      'source': tf.gather(TARGETS, tf.argmax(logits, 1)),
      'class': tf.argmax(logits, 1),
      'prob': tf.nn.softmax(logits)
    }

    if mode == tf.estimator.ModeKeys.TRAIN or mode == tf.estimator.ModeKeys.EVAL:
       loss = tf.losses.sparse_softmax_cross_entropy(labels, logits)
       eval_metrics = {'acc': tf.metrics.accuracy(tf.argmax(logits,1), labels)}
       train_op = tf.contrib.layers.optimize_loss(
         loss,
         tf.contrib.framework.get_global_step(),
         optimizer='Adam',
         learning_rate=0.01)
    else:
       loss = None
       train_op = None
       eval_metrics = None

    return tf.estimator.EstimatorSpec(
      mode=mode,
      predictions=predictions_dict,
      loss=loss,
      train_op=train_op,
      eval_metric_ops=eval_metrics,
      export_outputs={'classes': tf.estimator.export.PredictOutput(predictions_dict)}
    )


def serving_input_fn():
    feature_placeholders = {
      'title': tf.placeholder(tf.string, [None]),
    }
    features = {
      key: tf.expand_dims(tensor, -1)
      for key, tensor in feature_placeholders.items()
    }
    return tf.estimator.export.ServingInputReceiver(features, feature_placeholders)

def get_train(hparams):
  return read_dataset(hparams, 'train')

def get_valid(hparams, batch_size):
  return read_dataset(hparams, 'eval', batch_size=batch_size)


def init_embedding_hooks(hparams):
  if len(hparams['glove_embedding']) == 0:
     return None

  class InitEmbeddingHook(tf.train.SessionRunHook):
    def after_create_session(self, session, coord):
      PRETRAINED_EMBEDDING.init(session)       
  return [InitEmbeddingHook()]

from tensorflow.contrib.learn.python.learn.utils import saved_model_export_utils
def make_experiment_fn(output_dir, hparams):
  def experiment_fn(output_dir):
    # run experiment
    TRAIN_STEPS = hparams['train_steps']
    save_freq = max(1, min(200, TRAIN_STEPS/10))
    eval_freq = max(1, min(2000, TRAIN_STEPS/5))
    training_config = tf.contrib.learn.RunConfig(save_checkpoints_steps=save_freq,
                                                 save_checkpoints_secs=None)
    return tf.contrib.learn.Experiment(
        tf.estimator.Estimator(model_fn=cnn_model,
                               model_dir=output_dir,
                               config=training_config,
                               params=hparams),
        train_input_fn=get_train(hparams),
        eval_input_fn=get_valid(hparams, 2400),
        eval_steps = 10, # multiplied by batchsize should cover entire dataset
        export_strategies=[saved_model_export_utils.make_export_strategy(
            serving_input_fn,
            default_output_alternative_key=None,
            exports_to_keep=1
        )],
        train_steps = TRAIN_STEPS,
        train_monitors = init_embedding_hooks(hparams),
        eval_hooks = init_embedding_hooks(hparams)
    )
  return experiment_fn

