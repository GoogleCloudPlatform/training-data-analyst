# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Example implementation of image model in TensorFlow 
that can be trained and deployed on Cloud ML Engine
"""

import argparse
import json
import os

import model
import tensorflow as tf

def make_input_fn(csv_of_filenames, batch_size, augment):
  def read_lines(filename):
    from tensorflow.python.lib.io.file_io import FileIO
    with FileIO(filename, 'rb') as f:
      lines = f.readlines()
      return [line.rstrip() for line in lines]
   
  def _input_fn():
    filename_and_label = tf.train.string_input_producer(
                           string_tensor=read_lines(csv_of_filenames),
                           num_epochs=None)
    # get things one image and label at a time
    filename_and_label = filename_and_label.dequeue()
    filename, label = tf.decode_csv(filename_and_label,
                                   record_defaults=[['a'],['b']])
    #filename = tf.Print(filename, [filename, label], message='filename,label')

    # decode the image file starting from the filename
    # end up with pixel values that are in the -1, 1 range
    if batch_size != None:
       image = model.read_and_preprocess(filename)
    else:
       image = model.read_and_preprocess(filename)

    # covert 'roses' in the csv file to '2', for example
    labels_table = tf.contrib.lookup.index_table_from_tensor(
      tf.constant(model.LIST_OF_LABELS))
    label_int = labels_table.lookup(label)
    label_int = tf.reshape(label_int, [-1])

    # batch
    if batch_size != None:
       image, label_int = tf.train.shuffle_batch([image, label_int],
                             batch_size=batch_size, 
                             capacity=50*batch_size,
                             min_after_dequeue=20*batch_size,
                             enqueue_many=True)
    else:
       image, label_int = tf.train.batch([image, label_int],
                                         batch_size=1000,  # > number of eval samples
                                         enqueue_many=True,
                                         allow_smaller_final_batch=False)

    return {'image': image}, label_int  # features, label

  return _input_fn


def image_classifier(features, labels, mode, params):
  model_func = getattr(model, '{}_model'.format(params['model']))  # linear, dnn, cnn1, cnn2, etc.
  ylogits, nclasses = model_func(features['image'], mode, params)

  probabilities = tf.nn.softmax(ylogits)
  class_int = tf.cast(tf.argmax(probabilities, 1), tf.uint8)
  class_str = tf.gather(model.LIST_OF_LABELS, tf.cast(class_int, tf.int32))
  if mode == tf.estimator.ModeKeys.TRAIN or mode == tf.estimator.ModeKeys.EVAL:
    loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=ylogits, labels=tf.one_hot(labels, nclasses)))
    evalmetrics =  {'accuracy': tf.metrics.accuracy(class_int, labels)}
    if mode == tf.estimator.ModeKeys.TRAIN:
      # this is needed for batch normalization, but has no effect otherwise
      update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
      with tf.control_dependencies(update_ops):
         train_op = tf.contrib.layers.optimize_loss(loss, tf.train.get_global_step(),
                                                 learning_rate=params['learning_rate'], optimizer="Adam")
    else:
      train_op = None
  else:
    loss = None
    train_op = None
    evalmetrics = None
 
  return tf.estimator.EstimatorSpec(
        mode=mode,
        predictions={"probabilities": probabilities, "classid": class_int, "class": class_str},
        loss=loss,
        train_op=train_op,
        eval_metric_ops=evalmetrics,
        export_outputs={'classes': tf.estimator.export.PredictOutput({"probabilities": probabilities, "classid": class_int, "class": class_str})}
    )

def create_custom_estimator(output_dir, hparams):
  save_freq = max(1, min(100, hparams['train_steps']/10))
  training_config = tf.contrib.learn.RunConfig(save_checkpoints_secs=None,
                                               save_checkpoints_steps=save_freq)
  return tf.estimator.Estimator(model_fn=image_classifier, model_dir=output_dir, 
                                config=training_config, params=hparams)

def make_experiment_fn(output_dir, hparams):
  def experiment_fn(output_dir):
    eval_freq = max(1, min(2000, hparams['train_steps']/5))
    return tf.contrib.learn.Experiment(
      estimator=create_custom_estimator(output_dir, hparams),
      train_input_fn=make_input_fn('gs://cloud-ml-data/img/flower_photos/train_set.csv',
                                   hparams['train_batch_size'], hparams['augment']),
      eval_input_fn=make_input_fn('gs://cloud-ml-data/img/flower_photos/eval_set.csv',
                                   batch_size=None, augment=False),
      train_steps=hparams['train_steps'],
      eval_steps=1, # This multiplied by 1000 should cover complete dataset
      min_eval_frequency=eval_freq,
      export_strategies=tf.contrib.learn.utils.saved_model_export_utils.make_export_strategy(serving_input_fn=model.serving_input_fn)
    )
  return experiment_fn

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  # Input Arguments
  parser.add_argument(
      '--train_batch_size',
      help='Batch size for training steps',
      type=int,
      default=100
  )
  parser.add_argument(
      '--learning_rate',
      help='Initial learning rate for training',
      type=float,
      default=0.01
  )
  parser.add_argument(
      '--train_steps',
      help="""\
      Steps to run the training job for. A step is one batch-size,\
      """,
      type=int,
      default=0
  )
  parser.add_argument(
      '--output_dir',
      help='GCS location to write checkpoints and export models',
      required=True
  )
  model_names = [name.replace('_model','') \
                   for name in dir(model) \
                     if name.endswith('_model')]
  parser.add_argument(
      '--model',
      help='Type of model. Supported types are {}'.format(model_names),
      required=True
  )
  parser.add_argument(
      '--job-dir',
      help='this model ignores this field, but it is required by gcloud',
      default='junk'
  )

  parser.add_argument('--augment', help='if specified, augment image data', dest='augment', action='store_true'); parser.set_defaults(augment=False)

  # optional hyperparameters used by cnn
  parser.add_argument('--ksize1', help='kernel size of first layer for CNN', type=int, default=5)
  parser.add_argument('--ksize2', help='kernel size of second layer for CNN', type=int, default=5)
  parser.add_argument('--nfil1', help='number of filters in first layer for CNN', type=int, default=10)
  parser.add_argument('--nfil2', help='number of filters in second layer for CNN', type=int, default=20)
  parser.add_argument('--dprob', help='dropout probability for CNN', type=float, default=0.25)
  parser.add_argument('--batch_norm', help='if specified, do batch_norm for CNN', dest='batch_norm', action='store_true'); parser.set_defaults(batch_norm=False)

  args = parser.parse_args()
  hparams = args.__dict__
  
  # unused args provided by service
  hparams.pop('job_dir', None)
  hparams.pop('job-dir', None)

  output_dir = hparams.pop('output_dir')
  # Append trial_id to path for hptuning
  output_dir = os.path.join(
      output_dir,
      json.loads(
          os.environ.get('TF_CONFIG', '{}')
      ).get('task', {}).get('trial', '')
  )

  # calculate train_steps if not provided
  if hparams['train_steps'] < 1:
     # 10,000 steps at batch_size of 512
     hparams['train_steps'] = (10000 * 512) // hparams['train_batch_size']
     print "Training for {} steps".format(hparams['train_steps'])
  
  # Run the training job
  tf.contrib.learn.learn_runner.run(make_experiment_fn(output_dir, hparams), output_dir)

