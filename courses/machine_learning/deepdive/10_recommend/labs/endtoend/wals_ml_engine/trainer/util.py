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

import os
import uuid

import sh

import tensorflow as tf
from tensorflow.core.framework.summary_pb2 import Summary

def ensure_local_file(input_file):
  """
  Ensure the training ratings file is stored locally.
  """
  if input_file.startswith('gs:/'):
    input_path = os.path.join('/tmp/', str(uuid.uuid4()))
    os.makedirs(input_path)
    tmp_input_file = os.path.join(input_path, os.path.basename(input_file))
    sh.gsutil("cp", "-r", input_file, tmp_input_file)
    return tmp_input_file
  else:
    return input_file


def write_hptuning_metric(args, metric):
  """
  Write a summary containing the tuning loss metric, as required by hyperparam tuning.
  """
  summary = Summary(value=[Summary.Value(tag='training/hptuning/metric', simple_value=metric)])

  # for hyperparam tuning, we write a summary log to a directory 'eval' below the job directory
  eval_path = os.path.join(args['output_dir'], 'eval')
  summary_writer = tf.summary.FileWriter(eval_path)

  # Note: adding the summary to the writer is enough for hyperparam tuning.
  # The ml engine system is looking for any summary added with the hyperparam metric tag.
  summary_writer.add_summary(summary)
  summary_writer.flush()
