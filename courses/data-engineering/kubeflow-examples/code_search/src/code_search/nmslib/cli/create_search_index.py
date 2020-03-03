import csv
import logging
import os
import numpy as np
import tensorflow as tf

import code_search.nmslib.cli.arguments as arguments
import code_search.nmslib.search_engine as search_engine


def create_search_index(argv=None):
  """Create NMSLib index and a reverse lookup CSV file.

  This routine reads a list CSV data files at a given
  directory, combines them into one for reverse lookup
  and uses the embeddings string to create an NMSLib index.
  This embedding is the last column of all CSV files.

  Args:
    argv: A list of strings representing command line arguments.
  """
  tf.logging.set_verbosity(tf.logging.INFO)

  args = arguments.parse_arguments(argv)

  if not os.path.isdir(args.tmp_dir):
    logging.info("Creating directory %s", args.tmp_dir)
    os.makedirs(args.tmp_dir)

  tmp_index_file = os.path.join(args.tmp_dir, os.path.basename(args.index_file))
  tmp_lookup_file = os.path.join(args.tmp_dir, os.path.basename(args.lookup_file))

  embeddings_data = []

  with open(tmp_lookup_file, 'w') as lookup_file:
    lookup_writer = csv.writer(lookup_file)

    for csv_file_path in tf.gfile.Glob('{}/*index*.csv'.format(args.data_dir)):
      logging.info('Reading %s', csv_file_path)

      with tf.gfile.Open(csv_file_path) as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
          embedding_string = row[-1]
          embedding_vector = [float(value) for value in embedding_string.split(',')]
          embeddings_data.append(embedding_vector)

          lookup_writer.writerow(row[:-1])

  embeddings_data = np.array(embeddings_data)

  search_engine.CodeSearchEngine.create_index(embeddings_data, tmp_index_file)

  logging.info("Copying file %s to %s", tmp_lookup_file, args.lookup_file)
  tf.gfile.Copy(tmp_lookup_file, args.lookup_file)
  logging.info("Copying file %s to %s", tmp_index_file, args.index_file)
  tf.gfile.Copy(tmp_index_file, args.index_file)
  logging.info("Finished creating the index")


if __name__ == '__main__':
  logging.basicConfig(level=logging.INFO,
                      format=('%(levelname)s|%(asctime)s'
                              '|%(pathname)s|%(lineno)d| %(message)s'),
                      datefmt='%Y-%m-%dT%H:%M:%S',
                      )
  logging.getLogger().setLevel(logging.INFO)
  logging.info("Creating the search index")
  create_search_index()
