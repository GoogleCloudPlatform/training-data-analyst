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

# Import helpful libraries and setup our project, bucket, and region
import tensorflow as tf
import tensorflow_hub as hub
from tensorflow.python.lib.io import file_io

# Build hybrid recommendation neural network model
def build_model(args):
    # Get number of content ids from text file in Google Cloud Storage
    with file_io.FileIO(tf.gfile.Glob(filename = "gs://{}/hybrid_recommendation/preproc/vocab_counts/content_id_vocab_count.txt*".format(args['bucket']))[0], mode = 'r') as ifp:
        number_of_content_ids = int([x for x in ifp][0])
    print("number_of_content_ids = {}".format(number_of_content_ids))

    # Get number of categories from text file in Google Cloud Storage
    with file_io.FileIO(tf.gfile.Glob(filename = "gs://{}/hybrid_recommendation/preproc/vocab_counts/category_vocab_count.txt*".format(args['bucket']))[0], mode = 'r') as ifp:
        number_of_categories = int([x for x in ifp][0])
    print("number_of_categories = {}".format(number_of_categories))

    # Get number of authors from text file in Google Cloud Storage
    with file_io.FileIO(tf.gfile.Glob(filename = "gs://{}/hybrid_recommendation/preproc/vocab_counts/author_vocab_count.txt*".format(args['bucket']))[0], mode = 'r') as ifp:
        number_of_authors = int([x for x in ifp][0])
    print("number_of_authors = {}".format(number_of_authors))

    # Get mean months since epoch from text file in Google Cloud Storage
    with file_io.FileIO(tf.gfile.Glob(filename = "gs://{}/hybrid_recommendation/preproc/vocab_counts/months_since_epoch_mean.txt*".format(args['bucket']))[0], mode = 'r') as ifp:
        mean_months_since_epoch = float([x for x in ifp][0])
    print("mean_months_since_epoch = {}".format(mean_months_since_epoch))

    # Determine CSV and label columns
    NON_FACTOR_COLUMNS = 'next_content_id,visitor_id,content_id,category,title,author,months_since_epoch'.split(',')
    FACTOR_COLUMNS = ["user_factor_{}".format(i) for i in range(10)] + ["item_factor_{}".format(i) for i in range(10)]
    CSV_COLUMNS = NON_FACTOR_COLUMNS + FACTOR_COLUMNS
    LABEL_COLUMN = 'next_content_id'

    # Set default values for each CSV column
    NON_FACTOR_DEFAULTS = [["Unknown"],["Unknown"],["Unknown"],["Unknown"],["Unknown"],["Unknown"],[mean_months_since_epoch]]
    FACTOR_DEFAULTS = [[0.0] for i in range(10)]
    DEFAULTS = NON_FACTOR_DEFAULTS + (FACTOR_DEFAULTS + FACTOR_DEFAULTS) # user and item

    # Create input function for train and eval
    def read_dataset(filename, mode, batch_size = 512):
        def _input_fn():
            def decode_csv(value_column):
                columns = tf.decode_csv(records = value_column, record_defaults = DEFAULTS)
                features = dict(zip(CSV_COLUMNS, columns))          
                label = features.pop(LABEL_COLUMN)         
                return features, label

            # Create list of files that match pattern
            file_list = tf.gfile.Glob(filename = filename)

            # Create dataset from file list
            dataset = tf.data.TextLineDataset(filenames = file_list).map(map_func = decode_csv)

            if mode == tf.estimator.ModeKeys.TRAIN:
                num_epochs = None # indefinitely
                dataset = dataset.shuffle(buffer_size = 10 * batch_size)
            else:
                num_epochs = 1 # end-of-input after this

            dataset = dataset.repeat(count = num_epochs).batch(batch_size = batch_size)
            return dataset.make_one_shot_iterator().get_next()
        return _input_fn

    # Create feature columns to be used in model
    def create_feature_columns(args):
        # Create content_id feature column
        content_id_column = tf.feature_column.categorical_column_with_hash_bucket(
            key = "content_id",
            hash_bucket_size = number_of_content_ids)

        # Embed content id into a lower dimensional representation
        embedded_content_column = tf.feature_column.embedding_column(
            categorical_column = content_id_column,
            dimension = args['content_id_embedding_dimensions'])

        # Create category feature column
        categorical_category_column = tf.feature_column.categorical_column_with_vocabulary_file(
            key = "category",
            vocabulary_file = tf.gfile.Glob(filename = "gs://{}/hybrid_recommendation/preproc/vocabs/category_vocab.txt*".format(args['bucket']))[0],
            num_oov_buckets = 1)

        # Convert categorical category column into indicator column so that it can be used in a DNN
        indicator_category_column = tf.feature_column.indicator_column(categorical_column = categorical_category_column)

        # Create title feature column using TF Hub
        embedded_title_column = hub.text_embedding_column(
            key = "title", 
            module_spec = "https://tfhub.dev/google/nnlm-de-dim50-with-normalization/1",
            trainable = False)

        # Create author feature column
        author_column = tf.feature_column.categorical_column_with_hash_bucket(
            key = "author",
            hash_bucket_size = number_of_authors + 1)

        # Embed author into a lower dimensional representation
        embedded_author_column = tf.feature_column.embedding_column(
            categorical_column = author_column,
            dimension = args['author_embedding_dimensions'])

        # Create months since epoch boundaries list for our binning
        months_since_epoch_boundaries = list(range(400, 700, 20))

        # Create months_since_epoch feature column using raw data
        months_since_epoch_column = tf.feature_column.numeric_column(
            key = "months_since_epoch")

        # Create bucketized months_since_epoch feature column using our boundaries
        months_since_epoch_bucketized = tf.feature_column.bucketized_column(
            source_column = months_since_epoch_column,
            boundaries = months_since_epoch_boundaries)

        # Cross our categorical category column and bucketized months since epoch column
        crossed_months_since_category_column = tf.feature_column.crossed_column(
            keys = [categorical_category_column, months_since_epoch_bucketized],
            hash_bucket_size = len(months_since_epoch_boundaries) * (number_of_categories + 1))

        # Convert crossed categorical category and bucketized months since epoch column into indicator column so that it can be used in a DNN
        indicator_crossed_months_since_category_column = tf.feature_column.indicator_column(categorical_column = crossed_months_since_category_column)

        # Create user and item factor feature columns from our trained WALS model
        user_factors = [tf.feature_column.numeric_column(key = "user_factor_" + str(i)) for i in range(10)]
        item_factors =  [tf.feature_column.numeric_column(key = "item_factor_" + str(i)) for i in range(10)]

        # Create list of feature columns
        feature_columns = [embedded_content_column,
                           embedded_author_column,
                           indicator_category_column,
                           embedded_title_column,
                           indicator_crossed_months_since_category_column] + user_factors + item_factors

        return feature_columns

    # Create custom model function for our custom estimator
    def model_fn(features, labels, mode, params):
        # Create neural network input layer using our feature columns defined above
        net = tf.feature_column.input_layer(features = features, feature_columns = params['feature_columns'])

        # Create hidden layers by looping through hidden unit list
        for units in params['hidden_units']:
            net = tf.layers.dense(inputs = net, units = units, activation = tf.nn.relu)

        # Compute logits (1 per class) using the output of our last hidden layer
        logits = tf.layers.dense(inputs = net, units = params['n_classes'], activation = None)

        # Find the predicted classe indices based on the highest logit (which will result in the highest probability)
        predicted_classes = tf.argmax(input = logits, axis = 1)

        # Read in the content id vocabulary so we can tie the predicted class indices to their respective content ids
        with file_io.FileIO(tf.gfile.Glob(filename = "gs://{}/hybrid_recommendation/preproc/vocabs/content_id_vocab.txt*".format(params['bucket']))[0], mode = 'r') as ifp:
            content_id_names = tf.constant(value = [x.rstrip() for x in ifp])

        # Gather predicted class names based predicted class indices
        predicted_class_names = tf.gather(params = content_id_names, indices = predicted_classes)

        # If the mode is prediction
        if mode == tf.estimator.ModeKeys.PREDICT:
            # Create predictions dict
            predictions_dict = {
                'class_ids': tf.expand_dims(input = predicted_classes, axis = -1),
                'class_names' : tf.expand_dims(input = predicted_class_names, axis = -1),
                'probabilities': tf.nn.softmax(logits = logits),
                'logits': logits
            }

            # Create export outputs
            export_outputs = {"predict_export_outputs": tf.estimator.export.PredictOutput(outputs = predictions_dict)}

            return tf.estimator.EstimatorSpec( # return early since we're done with what we need for prediction mode
                mode = mode,
                predictions = predictions_dict,
                loss = None,
                train_op = None,
                eval_metric_ops = None,
                export_outputs = export_outputs)

        # Continue on with training and evaluation modes

        # Create lookup table using our content id vocabulary
        table = tf.contrib.lookup.index_table_from_file(
            vocabulary_file = tf.gfile.Glob(filename = "gs://{}/hybrid_recommendation/preproc/vocabs/content_id_vocab.txt*".format(params['bucket']))[0])

        # Look up labels from vocabulary table
        labels = table.lookup(keys = labels)

        # Compute loss using sparse softmax cross entropy since this is classification and our labels (content id indices) and probabilities are mutually exclusive
        loss = tf.losses.sparse_softmax_cross_entropy(labels = labels, logits = logits)

        # Compute evaluation metrics of total accuracy and the accuracy of the top k classes
        accuracy = tf.metrics.accuracy(labels = labels, predictions = predicted_classes, name = 'acc_op')
        top_k_accuracy = tf.metrics.mean(values = tf.nn.in_top_k(predictions = logits, targets = labels, k = params['top_k']))
        map_at_k = tf.metrics.average_precision_at_k(labels = labels, predictions = predicted_classes, k = params['top_k'])

        # Put eval metrics into a dictionary
        eval_metrics = {
            'accuracy': accuracy,
            'top_k_accuracy': top_k_accuracy,
            'map_at_k': map_at_k}

        # Create scalar summaries to see in TensorBoard
        tf.summary.scalar(name = 'accuracy', tensor = accuracy[1])
        tf.summary.scalar(name = 'top_k_accuracy', tensor = top_k_accuracy[1])
        tf.summary.scalar(name = 'map_at_k', tensor = map_at_k[1])

        # If the mode is evaluation
        if mode == tf.estimator.ModeKeys.EVAL:
            return tf.estimator.EstimatorSpec( # return early since we're done with what we need for evaluation mode
                mode = mode,
                predictions = None,
                loss = loss,
                train_op = None,
                eval_metric_ops = eval_metrics,
                export_outputs = None)

        # Continue on with training mode

        # If the mode is training
        assert mode == tf.estimator.ModeKeys.TRAIN

        # Create a custom optimizer
        optimizer = tf.train.AdagradOptimizer(learning_rate = params['learning_rate'])

        # Create train op
        train_op = optimizer.minimize(loss = loss, global_step = tf.train.get_global_step())

        return tf.estimator.EstimatorSpec( # final return since we're done with what we need for training mode
            mode = mode,
            predictions = None,
            loss = loss,
            train_op = train_op,
            eval_metric_ops = None,
            export_outputs = None)

    # Create serving input function
    def serving_input_fn():  
        feature_placeholders = {
            colname : tf.placeholder(dtype = tf.string, shape = [None]) \
            for colname in NON_FACTOR_COLUMNS[1:-1]
        }
        feature_placeholders['months_since_epoch'] = tf.placeholder(dtype = tf.float32, shape = [None])

        for colname in FACTOR_COLUMNS:
            feature_placeholders[colname] = tf.placeholder(dtype = tf.float32, shape = [None])

        features = {
            key: tf.expand_dims(tensor, -1) \
            for key, tensor in feature_placeholders.items()
        }

        return tf.estimator.export.ServingInputReceiver(features, feature_placeholders)

    # Create train and evaluate loop to combine all of the pieces together.
    tf.logging.set_verbosity(tf.logging.INFO)
    def train_and_evaluate(args):
        estimator = tf.estimator.Estimator(
            model_fn = model_fn,
            model_dir = args['output_dir'],
            params={
                'feature_columns': create_feature_columns(args),
                'hidden_units': args['hidden_units'],
                'n_classes': number_of_content_ids,
                'learning_rate': args['learning_rate'],
                'top_k': args['top_k'],
                'bucket': args['bucket']
            })

        train_spec = tf.estimator.TrainSpec(
            input_fn = read_dataset(filename = args['train_data_paths'], mode = tf.estimator.ModeKeys.TRAIN, batch_size = args['batch_size']),
            max_steps = args['train_steps'])

        exporter = tf.estimator.LatestExporter('exporter', serving_input_fn)

        eval_spec = tf.estimator.EvalSpec(
            input_fn = read_dataset(filename = args['eval_data_paths'], mode = tf.estimator.ModeKeys.EVAL, batch_size = args['batch_size']),
            steps = None,
            start_delay_secs = args['start_delay_secs'],
            throttle_secs = args['throttle_secs'],
            exporters = exporter)

        tf.estimator.train_and_evaluate(estimator, train_spec, eval_spec)
        
    # Call train_and_evaluate loop
    train_and_evaluate(args)
