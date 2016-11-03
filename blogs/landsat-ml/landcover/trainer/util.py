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
# ==============================================================================
"""Reusable utility functions.

This file is generic and can be reused by other models without modification.
"""

import multiprocessing
import os

import tensorflow as tf
from tensorflow.python.lib.io import file_io

FINAL_MODEL_DIR = 'model'
METADATA_FILE = 'metadata.yaml'


def _copy_all(src_files, dest_dir):
  # file_io.copy does not copy files into folders directly.
  for src_file in src_files:
    file_name = os.path.basename(src_file)
    new_file_location = os.path.join(dest_dir, file_name)
    file_io.copy(src_file, new_file_location)


def _recursive_copy(src_dir, dest_dir):
  """Copy the contents of src_dir into the folder dest_dir.

  When called, dest_dir should exist.
  """
  for dir_name, sub_dirs, leaf_files in file_io.walk(src_dir):
    # copy all the files over
    for leaf_file in leaf_files:
      leaf_file_path = os.path.join(dir_name, leaf_file)
      _copy_all([leaf_file_path], dest_dir)

    # Now make all the folders.
    for sub_dir in sub_dirs:
      file_io.create_dir(os.path.join(dest_dir, sub_dir))


class ExportLastModelMonitor(tf.contrib.learn.monitors.ExportMonitor):
  """Export the last model to its final location on GCS.

  The tf.learn ExportMonitor exports the models to a location based on the last
  n steps move the exported model to a fixed location.
  """

  def __init__(self,
               output_dir,
               final_model_location,
               additional_assets=None,
               input_fn=None,
               input_feature_key=None,
               exports_to_keep=5,
               signature_fn=None,
               default_batch_size=None):
    # Export the model to a temporary location then upload to its final
    # GCS destination.
    export_dir = os.path.join(output_dir, 'intermediate_models')
    super(ExportLastModelMonitor, self).__init__(
        every_n_steps=0,
        export_dir=export_dir,
        input_fn=input_fn,
        input_feature_key=input_feature_key,
        exports_to_keep=exports_to_keep,
        signature_fn=signature_fn,
        default_batch_size=default_batch_size)
    self._final_model_location = os.path.join(output_dir, final_model_location)
    self._additional_assets = additional_assets or []

  def every_n_step_end(self, step, outputs):
    # We only care about the last export.
    pass

  def end(self, session=None):
    super(ExportLastModelMonitor, self).end(session)
    # Recursively copy the last location export dir from the exporter into the
    # main export location.
    file_io.recursive_create_dir(self._final_model_location)
    _recursive_copy(self.last_export_dir, self._final_model_location)

    if self._additional_assets:
      # TODO(rhaertel): use the actual assets directory. For now, metadata.yaml
      # must be a sibling of the export.meta file.
      assets_dir = self._final_model_location
      file_io.create_dir(assets_dir)
      _copy_all(self._additional_assets, assets_dir)


def read_examples(input_files, batch_size, shuffle, num_epochs=None):
  """Creates readers and queues for reading example protos."""
  files = []
  for e in input_files:
    for path in e.split(','):
      files.extend(file_io.get_matching_files(path))
  thread_count = multiprocessing.cpu_count()

  # The minimum number of instances in a queue from which examples are drawn
  # randomly. The larger this number, the more randomness at the expense of
  # higher memory requirements.
  min_after_dequeue = 1000

  # When batching data, the queue's capacity will be larger than the batch_size
  # by some factor. The recommended formula is (num_threads + a small safety
  # margin). For now, we use a single thread for reading, so this can be small.
  queue_size_multiplier = thread_count + 3

  # Convert num_epochs == 0 -> num_epochs is None, if necessary
  num_epochs = num_epochs or None

  # Build a queue of the filenames to be read.
  filename_queue = tf.train.string_input_producer(files, num_epochs, shuffle)

  options = tf.python_io.TFRecordOptions(
      compression_type=tf.python_io.TFRecordCompressionType.GZIP)
  example_id, encoded_example = tf.TFRecordReader(options=options).read_up_to(
      filename_queue, batch_size)

  if shuffle:
    capacity = min_after_dequeue + queue_size_multiplier * batch_size
    return tf.train.shuffle_batch(
        [example_id, encoded_example],
        batch_size,
        capacity,
        min_after_dequeue,
        enqueue_many=True,
        num_threads=thread_count)

  else:
    capacity = queue_size_multiplier * batch_size
    return tf.train.batch(
        [example_id, encoded_example],
        batch_size,
        capacity=capacity,
        enqueue_many=True,
        num_threads=thread_count)


def override_if_not_in_args(flag, argument, args):
  """Checks if flags is in args, and if not it adds the flag to args."""
  if flag not in args:
    args.extend([flag, argument])
