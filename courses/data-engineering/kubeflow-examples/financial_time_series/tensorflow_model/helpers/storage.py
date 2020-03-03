"""Module that handles downloads and uploads to Google Cloud Storage.

Helpers functions to perform uploads and downloads from Google Cloud Storage.
"""
import os
from google.cloud import storage


def upload_to_storage(bucket, export_path):
  """Upload files from export path to Google Cloud Storage.

  Args:
    bucket (str): Google Cloud Storage bucket
    export_path (str): export path

  Returns:

  """
  client = storage.Client()
  bucket = client.get_bucket(bucket)
  if bucket:
    for root, _, files in os.walk(export_path):
      for file in files:
        path = os.path.join(root, file)
        blob = bucket.blob(path)
        blob.upload_from_filename(path)


def download_blob(bucket_name, source_blob_name, destination_file_name):
  """Downloads a blob from the bucket."""
  storage_client = storage.Client()
  bucket = storage_client.get_bucket(bucket_name)
  blob = bucket.blob(source_blob_name)

  blob.download_to_filename(destination_file_name)

  print('Blob {} downloaded to {}.'.format(
    source_blob_name,
    destination_file_name))


def list_blobs(bucket_name, prefix, delimiter=None):
  """Lists all the blobs in the bucket."""
  storage_client = storage.Client()
  return storage_client.list_blobs(bucket_name, prefix=prefix,
                                    delimiter=delimiter)
