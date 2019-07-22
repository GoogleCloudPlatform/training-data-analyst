import google.cloud.storage.client as gcs
import logging

def compose_shards(data, context):
  print(data)

  num_shards = 10
  prefix = 'flights/json/sharded/output'
  outfile = 'flights/json/flights.json'
  # trigger on the last file only
  filename = data['name']

  last_shard = '-%05d-of-%05d' % (num_shards - 1, num_shards)
  if (prefix in filename and last_shard in filename):
    # verify that all 10 shards exist
    prefix = filename.replace(last_shard, '')
    client = gcs.Client()
    bucket = client.bucket(data['bucket'])
    blobs = []
    for shard in range(num_shards):
      sfile = '%s-%05d-of-%05d' % (prefix, shard + 1, num_shards)
      blob = bucket.blob(sfile)
      if not blob.exists():
        # this causes a retry in 60s
        raise ValueError('Shard {} not present'.format(sfile))
      blobs.append(blob)
    # all shards exist, so compose
    bucket.blob(outfile).compose(blobs)
    logging.info('Successfully created {}'.format(outfile))
    for blob in blobs:
      blob.delete()
    logging.info('Deleted {} shards'.format(len(blobs)))

