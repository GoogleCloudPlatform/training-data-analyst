"""Module for running the training of the machine learning model.

Scripts that performs all the steps to train the ML model.
"""
import logging
import json
import os
import argparse
import time
import shutil
import sys
import pandas as pd
import tensorflow as tf
from tensorflow.python.lib.io import file_io

#pylint: disable=no-name-in-module
from helpers import preprocess, models, metrics
from helpers import storage as storage_helper


def parse_arguments(argv):
  """Parse command line arguments
  Args:
      argv (list): list of command line arguments including program name
  Returns:
      The parsed arguments as returned by argparse.ArgumentParser
  """
  parser = argparse.ArgumentParser(description='Training')

  parser.add_argument('--model',
                      type=str,
                      help='model to be used for training',
                      default='DeepModel',
                      choices=['FlatModel', 'DeepModel'])

  parser.add_argument('--epochs',
                      type=int,
                      help='number of epochs to train',
                      default=30001)

  parser.add_argument('--tag',
                      type=str,
                      help='tag of the model',
                      default='v1')

  parser.add_argument('--bucket',
                      type=str,
                      help='GCS bucket to store data and ML models',
                      default='<your-bucket-name>')

  parser.add_argument('--blob_path',
                      type=str,
                      help='GCS blob path where data is saved',
                      default='data')

  parser.add_argument('--kfp',
                      dest='kfp',
                      action='store_true',
                      help='Kubeflow pipelines flag')

  args, _ = parser.parse_known_args(args=argv[1:])

  return args


def run_training(argv=None):
  """Runs the ML model training.

  Args:
    args: args that are passed when submitting the training

  Returns:

  """
  # parse args
  args = parse_arguments(sys.argv if argv is None else argv)
  logging.info('getting the ML model...')
  model = getattr(models, args.model)(nr_predictors=24, nr_classes=2)

  # get the data
  logging.info('getting the data...')
  temp_folder = 'data'
  if not os.path.exists(temp_folder):
    os.mkdir(temp_folder)
  file_path = os.path.join(temp_folder, 'data.csv')
  storage_helper.download_blob(args.bucket, args.blob_path, file_path)
  time_series = pd.read_csv(file_path)
  training_test_data = preprocess.train_test_split(time_series, 0.8)


  # define training objective
  logging.info('defining the training objective...')
  sess = tf.Session()
  feature_data = tf.placeholder("float", [None, 24])
  actual_classes = tf.placeholder("float", [None, 2])

  model = model.build_model(feature_data)
  cost = -tf.reduce_sum(actual_classes * tf.log(model))
  train_opt = tf.train.AdamOptimizer(learning_rate=0.0001).minimize(cost)
  init = tf.global_variables_initializer()
  sess.run(init)

  # train model
  correct_prediction = tf.equal(tf.argmax(model, 1), tf.argmax(actual_classes, 1))
  accuracy = tf.reduce_mean(tf.cast(correct_prediction, "float"))

  logging.info('training the model...')
  time_dct = {}
  time_dct['start'] = time.time()
  for i in range(1, args.epochs):
    sess.run(
        train_opt,
        feed_dict={
            feature_data: training_test_data['training_predictors_tf'].values,
            actual_classes: training_test_data['training_classes_tf'].values.reshape(
                len(training_test_data['training_classes_tf'].values), 2)
        }
    )
    if i % 5000 == 0:
      train_acc = sess.run(
          accuracy,
          feed_dict={
              feature_data: training_test_data['training_predictors_tf'].values,
              actual_classes: training_test_data['training_classes_tf'].values.reshape(
                  len(training_test_data['training_classes_tf'].values), 2)
          }
      )
      print(i, train_acc)
  time_dct['end'] = time.time()
  logging.info('training took {0:.2f} sec'.format(time_dct['end'] - time_dct['start']))

  # print results of confusion matrix
  logging.info('validating model on test set...')
  feed_dict = {
      feature_data: training_test_data['test_predictors_tf'].values,
      actual_classes: training_test_data['test_classes_tf'].values.reshape(
          len(training_test_data['test_classes_tf'].values), 2)
  }
  test_acc = metrics.tf_confusion_matrix(model, actual_classes, sess,
                                         feed_dict)['accuracy']

  # create signature for TensorFlow Serving
  logging.info('Exporting model for tensorflow-serving...')

  export_path = os.path.join("models", args.tag)
  tf.saved_model.simple_save(
      sess,
      export_path,
      inputs={'predictors': feature_data},
      outputs={'prediction': tf.argmax(model, 1),
               'model-tag': tf.constant([str(args.tag)])}
  )

  # save model on GCS
  logging.info("uploading to " + args.bucket + "/" + export_path)
  storage_helper.upload_to_storage(args.bucket, export_path)

  if args.kfp:
    metrics_info = {
      'metrics': [{
          'name': 'accuracy-train',
          'numberValue': float(train_acc),
          'format': "PERCENTAGE"
      }, {
          'name': 'accuracy-test',
          'numberValue': float(test_acc),
          'format': "PERCENTAGE"
      }]}
    with file_io.FileIO('/mlpipeline-metrics.json', 'w') as f:
      json.dump(metrics_info, f)

    with open("/tmp/accuracy", "w") as output_file:
      output_file.write(str(float(test_acc)))

  # remove local files
  shutil.rmtree(export_path)
  shutil.rmtree(temp_folder)


if __name__ == '__main__':
  logging.basicConfig(level=logging.INFO)
  run_training()
