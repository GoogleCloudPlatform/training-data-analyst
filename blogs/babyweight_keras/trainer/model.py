# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Defines a Keras model and input function for training."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models


CSV_COLUMNS = 'weight_pounds,is_male,mother_age,plurality,gestation_weeks,key'.split(',')
SELECT_COLUMNS = 'weight_pounds,is_male,mother_age,plurality,gestation_weeks'.split(',')
LABEL_COLUMN = 'weight_pounds'


def read_dataset(bucket, prefix, pattern, batch_size=512, eval=False):
    # use prefix to create filename
    filename = 'gs://{}/babyweight/preproc/{}*{}*'.format(bucket, prefix, pattern)
    if eval:
        dataset = tf.data.experimental.make_csv_dataset(
            filename, header=False, batch_size=batch_size,
            shuffle=False, num_epochs=1,
            column_names=CSV_COLUMNS, label_name=LABEL_COLUMN,
            select_columns=SELECT_COLUMNS
        )
    else:
        dataset = tf.data.experimental.make_csv_dataset(
            filename, header=False, batch_size=batch_size,
            shuffle=True, num_epochs=None,
            column_names=CSV_COLUMNS, label_name=LABEL_COLUMN,
            select_columns=SELECT_COLUMNS
        )
    return dataset


def get_wide_deep():
    # defin model inputs
    inputs = {}
    inputs['is_male'] = layers.Input(shape=(), name='is_male', dtype='string')
    inputs['plurality'] = layers.Input(shape=(), name='plurality', dtype='string')
    inputs['mother_age'] = layers.Input(shape=(), name='mother_age', dtype='float32')
    inputs['gestation_weeks'] = layers.Input(shape=(), name='gestation_weeks', dtype='float32')

    # define column types
    is_male = tf.feature_column.categorical_column_with_vocabulary_list(
        'is_male', ['True', 'False', 'Unknown'])
    plurality = tf.feature_column.categorical_column_with_vocabulary_list(
        'plurality', ['Single(1)', 'Twins(2)', 'Triplets(3)', 'Quadruplets(4)', 'Quintuplets(5)', 'Multiple(2+)'])
    mother_age = tf.feature_column.numeric_column('mother_age')
    gestation_weeks = tf.feature_column.numeric_column('gestation_weeks')

    # discretize
    age_buckets = tf.feature_column.bucketized_column(
        mother_age, boundaries=np.arange(15, 45, 1).tolist())
    gestation_buckets = tf.feature_column.bucketized_column(
        gestation_weeks, boundaries=np.arange(17, 47, 1).tolist())

    # sparse columns are wide
    wide = [tf.feature_column.indicator_column(is_male),
            tf.feature_column.indicator_column(plurality),
            age_buckets,
            gestation_buckets]

    # feature cross all the wide columns and embed into a lower dimension
    crossed = tf.feature_column.crossed_column(
        [is_male, plurality, age_buckets, gestation_buckets], hash_bucket_size=20000)
    embed = tf.feature_column.embedding_column(crossed, 3)

    # continuous columns are deep
    deep = [mother_age,
            gestation_weeks,
            embed]

    return wide, deep, inputs


def create_keras_model(learning_rate=0.001):
    wide, deep, inputs = get_wide_deep()
    feature_layer_wide = layers.DenseFeatures(wide, name='wide_features')
    feature_layer_deep = layers.DenseFeatures(deep, name='deep_features')

    wide_model = feature_layer_wide(inputs)

    deep_model = layers.Dense(64, activation='relu', name='DNN_layer1')(feature_layer_deep(inputs))
    deep_model = layers.Dense(32, activation='relu', name='DNN_layer2')(deep_model)

    wide_deep_model = layers.Dense(1, name='weight')(layers.concatenate([wide_model, deep_model]))
    model = models.Model(inputs=inputs, outputs=wide_deep_model)

    # Compile Keras model
    model.compile(loss='mse', optimizer=tf.keras.optimizers.Adam(lr=learning_rate))
    return model
