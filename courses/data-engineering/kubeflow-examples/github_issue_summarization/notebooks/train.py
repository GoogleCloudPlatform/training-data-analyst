"""Train the github-issue-summarization model
train.py trains the github-issue-summarization model.

It reads the input data from GCS in a zip file format.
--input_data_gcs_bucket and --input_data_gcs_path specify
the location of input data.

It write the model back to GCS.
--output_model_gcs_bucket and --output_model_gcs_path specify
the location of output.

It also has parameters which control the training like
--learning_rate and --sample_size

"""
import argparse
import logging
import os
import re
import shutil
import time
import zipfile

import tempfile

from google.cloud import storage  # pylint: disable=no-name-in-module

import trainer

GCS_REGEX = re.compile("gs://([^/]*)(/.*)?")


def split_gcs_uri(gcs_uri):
  """Split a GCS URI into bucket and path."""
  m = GCS_REGEX.match(gcs_uri)
  bucket = m.group(1)
  path = ""
  if m.group(2):
    path = m.group(2).lstrip("/")
  return bucket, path

def is_gcs_path(gcs_uri):
  return GCS_REGEX.match(gcs_uri)

def process_input_file(remote_file):
  """Process the input file.

  If its a GCS file we download it to a temporary local file. We do this
  because Keras text preprocessing doesn't work with GCS.

  If its a zip file we unpack it.

  Args:
    remote_file: The input

  Returns:
    csv_file: The local csv file to process
  """
  if is_gcs_path(remote_file):
    # Download the input to a local
    with tempfile.NamedTemporaryFile() as hf:
      input_data = hf.name

    logging.info("Copying %s to %s", remote_file, input_data)
    input_data_gcs_bucket, input_data_gcs_path = split_gcs_uri(
      remote_file)

    logging.info("Download bucket %s object %s.", input_data_gcs_bucket,
                 input_data_gcs_path)
    bucket = storage.Bucket(storage.Client(), input_data_gcs_bucket)
    storage.Blob(input_data_gcs_path, bucket).download_to_filename(
      input_data)
  else:
    input_data = remote_file

  ext = os.path.splitext(input_data)[-1]
  if ext.lower() == '.zip':
    zip_ref = zipfile.ZipFile(input_data, 'r')
    zip_ref.extractall('.')
    zip_ref.close()
    # TODO(jlewi): Hardcoding the file in the Archive to use is brittle.
    # We should probably just require the input to be a CSV file.:
    csv_file = 'github_issues.csv'
  else:
    csv_file = input_data

  return csv_file

def wait_for_preprocessing(preprocessed_file):
  """Wait for preprocessing.

  In the case of distributed training the workers need to wait for the
  preprocessing to be completed. But only the master runs preprocessing.
  """
  # TODO(jlewi): Why do we need to block waiting for the file?
  # I think this is because only the master produces the npy
  # files so the other workers need to wait for the files to arrive.
  # It might be better to make preprocessing a separate job.
  # We should move this code since its only needed when using
  # TF.Estimator
  while True:
    if os.path.isfile(preprocessed_file):
      break
    logging.info("Waiting for dataset")
    time.sleep(2)

def main(unparsed_args=None):  # pylint: disable=too-many-statements
  # Parsing flags.
  parser = argparse.ArgumentParser()
  parser.add_argument("--sample_size", type=int, default=2000000)
  parser.add_argument("--num_epochs", type=int, default=7,
                      help="Number of training epochs.")
  parser.add_argument("--learning_rate", default=0.001, type=float)

  parser.add_argument(
    "--input_data",
    type=str,
    default="",
    help="The input location. Can be a GCS or local file path.")

  parser.add_argument(
    "--output_model",
    type=str,
    default="",
    help="The output location for the model GCS or local file path.")

  parser.add_argument(
    "--output_body_preprocessor_dpkl",
    type=str,
    default="body_pp.dpkl")
  parser.add_argument(
    "--output_title_preprocessor_dpkl",
    type=str,
    default="title_pp.dpkl")
  parser.add_argument(
    "--output_train_title_vecs_npy", type=str, default="train_title_vecs.npy")
  parser.add_argument(
    "--output_train_body_vecs_npy", type=str, default="train_body_vecs.npy")

  parser.add_argument(
    "--mode",
    type=str,
    default="keras",
    help="Whether to train using TF.estimator or Keras.")

  args = parser.parse_args(unparsed_args)

  logging.basicConfig(
    level=logging.INFO,
    format=('%(levelname)s|%(asctime)s'
            '|%(pathname)s|%(lineno)d| %(message)s'),
    datefmt='%Y-%m-%dT%H:%M:%S',
  )
  logging.getLogger().setLevel(logging.INFO)
  logging.info(args)


  mode = args.mode.lower()
  if not mode in ["estimator", "keras"]:
    raise ValueError("Unrecognized mode %s; must be keras or estimator" % mode)

  csv_file = process_input_file(args.input_data)

  # Use a temporary directory for all the outputs.
  # We will then copy the files to the final directory.
  output_dir = tempfile.mkdtemp()
  model_trainer = trainer.Trainer(output_dir)
  model_trainer.preprocess(csv_file, args.sample_size)

  if mode == "estimator":
    wait_for_preprocessing(model_trainer.preprocessed_bodies)

  model_trainer.build_model(args.learning_rate)

  # Tuples of (temporary, final) paths
  pairs = []

  if mode == "keras":
    local_model_output = args.output_model
    if is_gcs_path(args.output_model):
      local_model_output = os.path.join(output_dir, "model.h5")

    model_trainer.train_keras(local_model_output,
                              base_name=os.path.join(output_dir, "model-checkpoint"),
                              epochs=args.num_epochs)

    model_trainer.evaluate_keras()

    # With Keras we might need to write to a local directory and then
    # copy to GCS.
    pairs.append((local_model_output, args.output_model))
  elif mode == "estimator":
    # With TF.Estimator we should be able to write directly to GCS.
    model_trainer.train_estimator()

  pairs.extend([
    (model_trainer.body_pp_file, args.output_body_preprocessor_dpkl),
    (model_trainer.title_pp_file, args.output_title_preprocessor_dpkl),
    (model_trainer.preprocessed_titles, args.output_train_title_vecs_npy),
    (model_trainer.preprocessed_bodies, args.output_train_body_vecs_npy),])
  # Copy outputs
  for p in pairs:
    local = p[0]
    remote = p[1]
    if local == remote:
      continue

    logging.info("Copying %s to %s", local, remote)

    if is_gcs_path(remote):
      bucket_name, path = split_gcs_uri(remote)
      bucket = storage.Bucket(storage.Client(), bucket_name)
      blob = storage.Blob(path, bucket)
      blob.upload_from_filename(local)
    else:
      shutil.move(local, remote)

if __name__ == '__main__':
  main()
