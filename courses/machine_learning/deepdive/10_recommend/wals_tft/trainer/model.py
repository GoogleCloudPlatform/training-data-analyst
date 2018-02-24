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

import os
import shutil
import numpy as np
import tensorflow as tf
from tensorflow.python.lib.io import file_io
from tensorflow.contrib.factorization import WALSMatrixFactorization

tf.logging.set_verbosity(tf.logging.INFO)

def read_dataset(mode, args):
  def decode_example(protos, vocab_size):
    features = {'key': tf.FixedLenFeature([1], tf.int64),
                'indices': tf.VarLenFeature(dtype=tf.int64),
                'values': tf.VarLenFeature(dtype=tf.float32)}
    parsed_features = tf.parse_single_example(protos, features)
    keys = parsed_features['key']
    values = tf.sparse_merge(parsed_features['indices'], parsed_features['values'], vocab_size=vocab_size)
    return values
    
  def parse_tfrecords(filename, vocab_size):
    if mode == tf.estimator.ModeKeys.TRAIN:
        num_epochs = None # indefinitely
    else:
        num_epochs = 1 # end-of-input after this
    
    files = tf.gfile.Glob(os.path.join(args['input_path'], filename))
    
    # Create dataset from file list
    dataset = tf.data.TFRecordDataset(files)
    dataset = dataset.map(lambda x: decode_example(x, vocab_size))
    dataset = dataset.repeat(num_epochs)
    dataset = dataset.batch(args['batch_size'])
    return dataset.make_one_shot_iterator().get_next()
  
  def parse_tfrecords_new(filename, vocab_size):
    if mode == tf.estimator.ModeKeys.TRAIN:
        batch_size = args['batch_size']
    else:
        batch_size = 1
    
    parsed_features = tf.contrib.learn.io.read_batch_features(
      os.path.join(args['input_path'], filename),
      batch_size, 
      {'key': tf.FixedLenFeature([1], tf.int64),
                'indices': tf.VarLenFeature(dtype=tf.int64),
                'values': tf.VarLenFeature(dtype=tf.float32)},
      tf.TFRecordReader
    )
    keys = parsed_features['key']
    values = tf.sparse_merge(parsed_features['indices'], 
                             parsed_features['values'], 
                             vocab_size=vocab_size)
    return values
  
  def _input_fn():
    features = {
      WALSMatrixFactorization.INPUT_ROWS: parse_tfrecords('items_for_user*', args['nitems']),
      WALSMatrixFactorization.INPUT_COLS: parse_tfrecords('users_for_item*', args['nusers']),
      WALSMatrixFactorization.PROJECT_ROW: tf.constant(True)
    }
    return features, None
  
  # just for developing line by line. You don't need this in production
  def _input_fn_subset():
    features = {
      WALSMatrixFactorization.INPUT_ROWS: parse_tfrecords('items_for_user-00001-*', args['nitems']),
      WALSMatrixFactorization.PROJECT_ROW: tf.constant(True)
    }
    return features, None
  
  return _input_fn#_subset

def find_top_k(user, item_factors, k):
  all_items = tf.matmul(tf.expand_dims(user, 0), tf.transpose(item_factors))
  topk = tf.nn.top_k(all_items, k=k)
  return tf.cast(topk.indices, dtype=tf.int64)
    
def batch_predict(args):
  import numpy as np
  
  # read vocabulary into Python list for quick index-ed lookup
  def create_lookup(filename):
      from tensorflow.python.lib.io import file_io
      dirname = os.path.join(args['input_path'], 'transform_fn/transform_fn/assets/')
      with file_io.FileIO(os.path.join(dirname, filename), mode='r') as ifp:
        return [x.rstrip() for x in ifp]
  originalItemIds = create_lookup('vocab_items')
  originalUserIds = create_lookup('vocab_users')
  
  with tf.Session() as sess:
    estimator = tf.contrib.factorization.WALSMatrixFactorization(
                         num_rows=args['nusers'], num_cols=args['nitems'],
                         embedding_dimension=args['n_embeds'],
                         model_dir=args['output_dir'])
           
    # but for in-vocab data, the row factors are already in the checkpoint
    user_factors = tf.convert_to_tensor(estimator.get_row_factors()[0]) # (nusers, nembeds)
    # in either case, we have to assume catalog doesn't change, so col_factors are read in
    item_factors = tf.convert_to_tensor(estimator.get_col_factors()[0])# (nitems, nembeds)
    
    # for each user, find the top K items
    topk = tf.squeeze(tf.map_fn(lambda user: find_top_k(user, item_factors, args['topk']), 
                                user_factors, dtype=tf.int64))
    with file_io.FileIO(os.path.join(args['output_dir'], 'batch_pred.txt'), mode='w') as f:
      for userId, best_items_for_user in enumerate(topk.eval()):
        f.write(originalUserIds[userId] + '\t') # write userId \t item1,item2,item3...
        f.write(','.join(originalItemIds[itemId] for itemId in best_items_for_user) + '\n')

# online prediction returns row and column factors as needed
def create_serving_input_fn(args):
  def for_user_embeddings(originalUserId):
      # convert the userId that the end-user provided to integer
      originalUserIds = tf.contrib.lookup.index_table_from_file(
          os.path.join(args['input_path'], 'transform_fn/transform_fn/assets/vocab_users'))
      userId = originalUserIds.lookup(originalUserId)
      
      # all items for this user (for user_embeddings)
      items = tf.range(args['nitems'], dtype=tf.int64)
      users = userId * tf.ones([args['nitems']], dtype=tf.int64)
      ratings = 0.1 * tf.ones_like(users, dtype=tf.float32)
      return items, users, ratings, tf.constant(True)
    
  def for_item_embeddings(originalItemId):
      # convert the userId that the end-user provided to integer
      originalItemIds = tf.contrib.lookup.index_table_from_file(
          os.path.join(args['input_path'], 'transform_fn/transform_fn/assets/vocab_items'))
      itemId = originalItemIds.lookup(originalItemId)
    
      # all users for this item (for item_embeddings)
      users = tf.range(args['nusers'], dtype=tf.int64)
      items = itemId * tf.ones([args['nusers']], dtype=tf.int64)
      ratings = 0.1 * tf.ones_like(users, dtype=tf.float32)
      return items, users, ratings, tf.constant(False)
    
  def serving_input_fn():
    feature_ph = {
        #'visitorId': tf.constant(['1000923781653568442']),
        #'contentId': tf.constant([''])
        'visitorId': tf.placeholder(tf.string, [1], name='visitorId'),
        'contentId': tf.placeholder(tf.string, [1], name='contentId')
    }

    (items, users, ratings, project_row) = \
                  tf.cond(tf.equal(feature_ph['visitorId'][0], tf.constant("", dtype=tf.string)),
                          lambda: for_item_embeddings(feature_ph['contentId']),
                          lambda: for_user_embeddings(feature_ph['visitorId']))
    rows = tf.stack( [users, items], axis=1 )
    cols = tf.stack( [items, users], axis=1 )
    input_rows = tf.SparseTensor(rows, ratings, (args['nusers'], args['nitems']))
    input_cols = tf.SparseTensor(cols, ratings, (args['nusers'], args['nitems']))
    
    features = {
      WALSMatrixFactorization.INPUT_ROWS: input_rows,
      WALSMatrixFactorization.INPUT_COLS: input_cols,
      WALSMatrixFactorization.PROJECT_ROW: project_row
    }
    return tf.contrib.learn.InputFnOps(features, None, feature_ph)

  return serving_input_fn
        
def train_and_evaluate(args):
    train_steps = int(0.5 + (1.0 * args['num_epochs'] * args['nusers']) / args['batch_size'])
    steps_in_epoch = int(0.5 + args['nusers'] / args['batch_size'])
    print('Will train for {} steps, evaluating once every {} steps'.format(train_steps, steps_in_epoch))
    def experiment_fn(output_dir):
        return tf.contrib.learn.Experiment(
            tf.contrib.factorization.WALSMatrixFactorization(
                         num_rows=args['nusers'], num_cols=args['nitems'],
                         embedding_dimension=args['n_embeds'],
                         model_dir=args['output_dir']),
            train_input_fn=read_dataset(tf.estimator.ModeKeys.TRAIN, args),
            eval_input_fn=read_dataset(tf.estimator.ModeKeys.EVAL, args),
            train_steps=train_steps,
            eval_steps=1,
            min_eval_frequency=steps_in_epoch,
            export_strategies=tf.contrib.learn.utils.saved_model_export_utils.make_export_strategy(serving_input_fn=create_serving_input_fn(args))
        )

    from tensorflow.contrib.learn.python.learn import learn_runner
    learn_runner.run(experiment_fn, args['output_dir'])
    
    batch_predict(args)

