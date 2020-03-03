# Copyright 2018 Google Inc. All Rights Reserved.
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



import argparse
import json
import logging
import subprocess
import time
from urlparse import urlparse

from google.cloud import storage
import pathlib2


COPY_ACTION = 'copy_data'
TRAIN_ACTION = 'train'
PROBLEM = 'gh_problem'
OUTPUT_PATH = '/tmp/output'


def copy_blob(storage_client, source_bucket, source_blob, target_bucket_name, new_blob_name,
    new_blob_prefix, prefix):
  """Copies a blob from one bucket to another with a new name."""

  target_bucket = storage_client.get_bucket(target_bucket_name)
  new_blob_name_trimmed = new_blob_name.replace(prefix, '')
  new_blob_full_name = new_blob_prefix + '/'+ new_blob_name_trimmed

  new_blob = source_bucket.copy_blob(
      source_blob, target_bucket, new_blob_full_name)

  logging.info('blob %s in bucket %s copied to blob %s in bucket %s',
      str(source_blob.name), str(source_bucket.name), str(new_blob.name), str(target_bucket.name))


def copy_checkpoint(checkpoint_dir, model_dir):
  """Copy an existing model checkpoint directory to the working directory for the workflow,
  so that the training can start from that point.
  """

  storage_client = storage.Client()
  retries = 10

  source_bucket_string = urlparse(checkpoint_dir).netloc
  source_prefix = checkpoint_dir.replace('gs://' + source_bucket_string + '/', '')
  logging.info("source bucket %s and prefix %s", source_bucket_string, source_prefix)
  source_bucket = storage_client.bucket(source_bucket_string)

  target_bucket = urlparse(model_dir).netloc
  logging.info("target bucket: %s", target_bucket)
  new_blob_prefix = model_dir.replace('gs://' + target_bucket + '/', '')
  logging.info("new_blob_prefix: %s", new_blob_prefix)

  # Lists objects with the given prefix.
  blob_list = list(source_bucket.list_blobs(prefix=source_prefix))
  logging.info('Copying files:')
  for blob in blob_list:
    sleeptime = 0.1
    num_retries = 0
    while num_retries < retries:
      logging.info('copying %s; retry %s', blob.name, num_retries)
      try:
        copy_blob(storage_client, source_bucket, blob, target_bucket, blob.name, new_blob_prefix,
            source_prefix)
        break
      except Exception as e:  #pylint: disable=broad-except
        logging.warning(e)
        time.sleep(sleeptime)
        sleeptime *= 2
        num_retries += 1

def run_training(args, data_dir, model_dir, problem):
  """Run the model training, and when finished export the results."""

  if not args.train_steps:
    logging.error("Number of training steps not set.")
    return
  print('training steps (total): %s' % args.train_steps)

  # Run the training for N steps.
  model_train_command = ['t2t-trainer', '--data_dir', data_dir,
     '--t2t_usr_dir', '/ml/ghsumm/trainer',
     '--problem', problem,
     '--model', 'transformer', '--hparams_set', 'transformer_prepend', '--output_dir', model_dir,
     '--job-dir', model_dir,
     '--train_steps', args.train_steps, '--eval_throttle_seconds', '240',
     ]
  print(model_train_command)
  result2 = subprocess.call(model_train_command)  # pylint: disable=unused-variable
  # print(result2)

  # then export the model...
  model_export_command = ['t2t-exporter', '--model', 'transformer',
      '--hparams_set', 'transformer_prepend',
      '--problem', problem,
      '--t2t_usr_dir', '/ml/ghsumm/trainer', '--data_dir', data_dir, '--output_dir', model_dir]
  print(model_export_command)
  result3 = subprocess.call(model_export_command)  # pylint: disable=unused-variable
  # print(result3)

  print("deploy-webapp arg: %s" % args.deploy_webapp)
  with open(OUTPUT_PATH, 'w') as f:
    f.write(args.deploy_webapp)


def main():

  logging.getLogger().setLevel(logging.INFO)
  parser = argparse.ArgumentParser(description='ML Trainer')
  parser.add_argument(
      '--model-dir',
      help='...',
      required=True)
  parser.add_argument(
      '--action',
      help='...',
      required=True)
  parser.add_argument(
      '--data-dir',
      help='...',
      required=True)
  parser.add_argument(
      '--copy-output-path',
      help='...',
      )
  parser.add_argument(
      '--train-output-path',
      help='...',
      )
  parser.add_argument(  # used for the copy step only
      '--checkpoint-dir',
      help='...',
      required=False)
  parser.add_argument(
      '--train-steps',
      help='...')
  parser.add_argument(
      '--deploy-webapp',
      help='...',
      default='true')

  args = parser.parse_args()

  data_dir = args.data_dir
  logging.info("data dir: %s", data_dir)
  model_dir = args.model_dir
  logging.info("model_dir: %s", model_dir)

  if args.action.lower() == COPY_ACTION:
    logging.info("model starting checkpoint: %s", args.checkpoint_dir)
    copy_checkpoint(args.checkpoint_dir, model_dir)
    # write the model dir path as an output param
    logging.info("copy_output_path: %s", args.copy_output_path)
    pathlib2.Path(args.copy_output_path).parent.mkdir(parents=True)
    pathlib2.Path(args.copy_output_path).write_text(model_dir.decode('utf-8'))

  elif args.action.lower() == TRAIN_ACTION:
    # launch the training job
    run_training(args, data_dir, model_dir, PROBLEM)
    # write the model export path as an output param
    logging.info("train_output_path: %s", args.train_output_path)
    pathlib2.Path(args.train_output_path).parent.mkdir(parents=True)
    export_dir = '%s/export' % model_dir
    pathlib2.Path(args.train_output_path).write_text(export_dir.decode('utf-8'))
    # Create metadata.json file for Tensorboard 'artifact'
    metadata = {
      'outputs' : [{
        'type': 'tensorboard',
        'source': model_dir,
      }]
    }
    with open('/mlpipeline-ui-metadata.json', 'w') as f:
      json.dump(metadata, f)

  else:
    logging.warning("Error: unknown action mode %s", args.action)



if __name__ == "__main__":
  main()
