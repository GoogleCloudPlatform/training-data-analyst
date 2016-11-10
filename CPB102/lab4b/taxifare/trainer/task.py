# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Example implementation of code to run on the Cloud ML service.
"""
import argparse
import json
import logging
import os
import time

import taxifare
import tensorflow as tf
from tensorflow.contrib.metrics.python.ops import metric_ops

import google.cloud.ml.features as features


def main():
  config = json.loads(os.environ.get('TF_CONFIG', '{}'))
  cluster = config.get('cluster', None)
  task = config.get('task', None)
  job = config.get('job', None)
  trial_id = task.get('trial', '')

  parser = argparse.ArgumentParser()
  parser.add_argument('--train_data_paths', type=str)
  parser.add_argument('--eval_data_paths', type=str)
  parser.add_argument('--metadata_path', type=str)
  parser.add_argument('--output_path', type=str)
  parser.add_argument('--max_steps', type=int, default=2000)
  parser.add_argument('--number_buckets', type=int, default=5)
  parser.add_argument('--hidden_layer1_size', type=int, default=256)
  parser.add_argument('--batch_size', type=int, default=128)
  parser.add_argument('--learning_rate', type=float, default=0.01)

  args = parser.parse_args()
  HYPERPARAMS['batch_size'] = args.batch_size
  HYPERPARAMS['learning_rate'] = args.learning_rate
  HYPERPARAMS['hidden_layer1_size'] = args.hidden_layer1_size
  HYPERPARAMS['hidden_layer2_size'] = args.hidden_layer1_size / 2
  HYPERPARAMS['hidden_layer3_size'] = args.hidden_layer1_size / 4
  HYPERPARAMS['number_buckets'] = args.number_buckets
  
  args.output_path = os.path.join(args.output_path, trial_id)
  logging.info("start trial %s outputs in %s", trial_id, args.output_path)

  dispatch(args, cluster, task, job)

EXPORT_SUBDIRECTORY = 'model'
HYPERPARAMS = {
  'batch_size': 128,
  'learning_rate': 0.01,
  'hidden_layer1_size': 300,
  'hidden_layer2_size': 200,
  'hidden_layer3_size': 100,
  'number_buckets': 5
}
EVAL_SET_SIZE = 2767
EVAL_INTERVAL_SECS = 30


def start_server(cluster, task):
  # Create and start a server.
  return tf.train.Server(cluster,
                         protocol='grpc',
                         job_name=task['type'],
                         task_index=task['index'])


def dispatch(args, cluster, task, job):
  if not cluster:
    # Run locally.
    run_training(args, target='', is_chief=True, device_fn='')
    return

  if task['type'] == 'ps':
    server = start_server(cluster, task)
    server.join()
  elif task['type'] == 'worker':
    server = start_server(cluster, task)
    is_chief = False
    device_fn = tf.train.replica_device_setter(
        ps_device='/job:ps',
        worker_device='/job:worker/task:%d' % task['index'],
        cluster=cluster)
    run_training(args, server.target, is_chief, device_fn)
  elif task['type'] == 'master':
    server = start_server(cluster, task)
    is_chief = (task['index'] == 0)
    device_fn = tf.train.replica_device_setter(
        ps_device='/job:ps',
        worker_device='/job:master/task:%d' % task['index'],
        cluster=cluster)
    run_training(args, server.target, is_chief, device_fn)
  else:
    raise ValueError('invalid job_type %s' % task['type'])


def run_training(args, target, is_chief, device_fn):
  """Train Census for a number of steps."""
  # Get the sets of examples and targets for training, validation, and
  # test on Census.
  training_data = args.train_data_paths

  if is_chief:
    # A generator over accuracies. Each call to next(accuracies) forces an
    # evaluation of the model.
    accuracies = evaluate(args)

  # Tell TensorFlow that the model will be built into the default Graph.
  with tf.Graph().as_default() as graph:
    # Assigns ops to the local worker by default.
    with tf.device(device_fn):

      metadata = features.FeatureMetadata.get_metadata(args.metadata_path)

      _, train_examples = taxifare.read_examples(
          training_data, HYPERPARAMS['batch_size'], shuffle=False)

      # Generate placeholders for the examples.
      placeholder, inputs, targets, _ = (
          taxifare.create_inputs(metadata, train_examples, HYPERPARAMS))

      # Build a Graph that computes predictions from the inference model.
      output = taxifare.inference(inputs, metadata, HYPERPARAMS)

      # Add to the Graph the Ops for loss calculation.
      loss = taxifare.loss(output, targets)

      # Add to the Graph the Ops that calculate and apply gradients.
      train_op, global_step = taxifare.training(loss,
                                              HYPERPARAMS['learning_rate'])

      # Build the summary operation based on the TF collection of Summaries.
      summary_op = tf.merge_all_summaries()

      # Add the variable initializer Op.
      init_op = tf.initialize_all_variables()

      # Create a saver for writing training checkpoints.
      saver = tf.train.Saver()

      # Instantiate a SummaryWriter to output summaries and the Graph.
      summary_writer = tf.train.SummaryWriter(os.path.join(
          args.output_path, 'summaries'), graph)

      # Create a "supervisor", which oversees the training process.
      sv = tf.train.Supervisor(is_chief=is_chief,
                               logdir=os.path.join(args.output_path, 'logdir'),
                               init_op=init_op,
                               saver=saver,
                               summary_op=None,
                               global_step=global_step,
                               save_model_secs=60)

      # The supervisor takes care of session initialization, restoring from
      # a checkpoint, and closing when done or an error occurs.
      logging.info('Starting the loop.')
      with sv.managed_session(target) as sess:
        start_time = time.time()
        last_save = start_time

        # Loop until the supervisor shuts down or max_steps have completed.
        step = 0
        while not sv.should_stop() and step < args.max_steps:
          start_time = time.time()

          # Run one step of the model.  The return values are the activations
          # from the `train_op` (which is discarded) and the `loss` Op.  To
          # inspect the values of your Ops or variables, you may include them
          # in the list passed to sess.run() and the value tensors will be
          # returned in the tuple from the call.
          _, step, loss_value = sess.run([train_op, global_step, loss])

          duration = time.time() - start_time
          if is_chief and time.time() - last_save > EVAL_INTERVAL_SECS:
            last_save = time.time()
            saver.save(sess, sv.save_path, global_step)
            rmse = next(accuracies)
            logging.info('Eval, step %d: rmse = %0.3f', step, rmse)

          # Write the summaries and log an overview fairly often.
          if step % 100 == 0 and is_chief:
            # Log status.
            logging.info('Step %d: loss = %.2f (%.3f sec)', step, loss_value,
                         duration)

            # Update the events file.
            summary_str = sess.run(summary_op)
            summary_writer.add_summary(summary_str, step)
            summary_writer.flush()

        if is_chief:
          # Force a save at the end of our loop.
          sv.saver.save(sess, sv.save_path, global_step=global_step,
                        write_meta_graph=False)

          logging.info('Final rmse after %d steps = %0.3f', step,
                 next(accuracies))

          # Save the model for inference
          export_model(args, sess, sv.saver)

      # Ask for all the services to stop.
      sv.stop()
      logging.info('Done training.')


def export_model(args, sess, training_saver):
  with tf.Graph().as_default() as inference_graph:
    metadata = features.FeatureMetadata.get_metadata(args.metadata_path)
    placeholder, inputs, _, keys = taxifare.create_inputs(metadata, None, HYPERPARAMS)
    output = taxifare.inference(inputs, metadata, HYPERPARAMS)

    inference_saver = tf.train.Saver()

    # Mark the inputs and the outputs
    tf.add_to_collection('inputs',
                         json.dumps({'examples': placeholder.name}))
    tf.add_to_collection('outputs',
                         json.dumps({'key': keys.name,
                                     'score': output.name}))

    model_dir = os.path.join(args.output_path, EXPORT_SUBDIRECTORY)

    # We need to save the variables from the training session, but we need
    # to serialize the serving graph.

    # Serialize the graph (MetaGraphDef)
    inference_saver.export_meta_graph(
        filename=os.path.join(model_dir, 'export.meta'))

    # Save the variables. Don't write the MetaGraphDef, because that is
    # actually the training graph.
    training_saver.save(sess,
                        os.path.join(model_dir, 'export'),
                        write_meta_graph=False)


def evaluate(args):
  """Run one round of evaluation, yielding rmse."""

  eval_data = args.eval_data_paths

  with tf.Graph().as_default() as g:
    metadata = features.FeatureMetadata.get_metadata(args.metadata_path)

    _, examples = taxifare.read_examples(
        eval_data, HYPERPARAMS['batch_size'],
        shuffle=False, num_epochs=1)

    # Generate placeholders for the examples.
    placeholder, inputs, targets, _ = (
        taxifare.create_inputs(metadata, examples, HYPERPARAMS))

    # Build a Graph that computes predictions from the inference model.
    output = taxifare.inference(inputs, metadata, HYPERPARAMS)

    # Add to the Graph the Ops for loss calculation.
    loss = taxifare.loss(output, targets)

    # Add the Op to compute rmse.
    rmse_op, eval_op = metric_ops.streaming_root_mean_squared_error(
        output, targets)

    # The global step is useful for summaries.
    with tf.name_scope('train'):
      global_step = tf.Variable(0, name='global_step', trainable=False)

    tf.scalar_summary('rmse', rmse_op)
    tf.scalar_summary('training/hptuning/metric', rmse_op)
    summary = tf.merge_all_summaries() # make sure all scalar summaries are produced

    saver = tf.train.Saver()

  # Setting num_eval_batches isn't strictly necessary, as the file reader does
  # at most one epoch.
  num_eval_batches = float(EVAL_SET_SIZE) // HYPERPARAMS['batch_size']
  summary_writer = tf.train.SummaryWriter(os.path.join(
      args.output_path, 'eval'))
  sv = tf.train.Supervisor(graph=g,
                           logdir=os.path.join(args.output_path, 'eval'),
                           summary_op=summary,
                           summary_writer=summary_writer,
                           global_step=None,
                           saver=saver)

  step = 0
  while step < args.max_steps:
    last_checkpoint = tf.train.latest_checkpoint(os.path.join(
        args.output_path, 'logdir'))
    with sv.managed_session(master='',
                            start_standard_services=False) as session:
      sv.start_queue_runners(session)
      sv.saver.restore(session, last_checkpoint)
      rmse = tf_evaluation(session,
                               max_num_evals=num_eval_batches,
                               eval_op=eval_op,
                               final_op=rmse_op,
                               summary_op=summary,
                               summary_writer=summary_writer,
                               global_step=global_step)

      step = tf.train.global_step(session, global_step)
      yield rmse


def tf_evaluation(sess,
                  max_num_evals=1000,
                  eval_op=None,
                  final_op=None,
                  summary_op=None,
                  summary_writer=None,
                  global_step=None):
  """Performs a single evaluation run.

  A single evaluation consists of several steps run in the following order:
  (1) an evaluation op which is executed `num_evals` times (2) a finalization
  op and (3) the execution of a summary op which is
  written out using a summary writer.

  Args:
    sess: The current Tensorflow `Session`.
    max_num_evals: The number of times to execute `eval_op`.
    eval_op: A operation run `num_evals` times.
    final_op: An operation to execute after all of the `eval_op` executions. The
      value of `final_op` is returned.
    summary_op: A summary op executed after `eval_op` and `finalize_op`.
    summary_writer: The summery writer used if `summary_op` is provided.
    global_step: the global step variable. If left as `None`, then
      slim.variables.global_step() is used.

  Returns:
    The value of `final_op` or `None` if `final_op` is `None`.

  Raises:
    ValueError: if `summary_op` is provided but `global_step` is `None`.
  """
  if eval_op is not None:
    try:
      for i in range(int(max_num_evals)):
        (_, final_op_value) = sess.run((eval_op, final_op))
    except tf.errors.OutOfRangeError:
      # We've hit the end of our epoch.  Unfortunately, if we hit this
      # tensorflow has already logged a warning to stderr, so we try to avoid
      # hitting it in this sample.
      pass

  if summary_op is not None:
    if global_step is None:
      raise ValueError('must specify global step')

    global_step = tf.train.global_step(sess, global_step)
    summary = sess.run(summary_op)
    summary_writer.add_summary(summary, global_step)
    summary_writer.flush()

  return final_op_value

if __name__ == '__main__':
  logging.basicConfig(level=logging.INFO)
  main()

