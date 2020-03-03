# TODO(jlewi): We import nmslib at the top as a hack to fix the error
# ImportError: dlopen: cannot load any more object with static TLS.
# We get this error when running inside a docker container. Moving the
# import to the top of the file seems to work around this.
import nmslib # pylint: disable=unused-import

import csv  # pylint: disable=wrong-import-order
import logging  # pylint: disable=wrong-import-order
import json  # pylint: disable=wrong-import-order
import os  # pylint: disable=wrong-import-order
import functools # pylint: disable=wrong-import-order
import requests  # pylint: disable=wrong-import-order
import tensorflow as tf

import code_search.nmslib.cli.arguments as arguments
import code_search.t2t.query as query
# We need to import function_docstring to ensure the problem is registered
from code_search.t2t import function_docstring # pylint: disable=unused-import
from code_search.nmslib.search_engine import CodeSearchEngine
from code_search.nmslib.search_server import CodeSearchServer


def embed_query(encoder, serving_url, query_str):
  data = {"instances": [{"input": {"b64": encoder(query_str)}}]}

  logging.info("Sending request to: %s", serving_url)
  response = requests.post(url=serving_url,
                           headers={'content-type': 'application/json'},
                           data=json.dumps(data))

  if not response.ok:
    logging.error("Request failed; status: %s reason %s response: %s",
                  response.status_code,
                  response.reason,
                  response.content)
  result = response.json()
  return result['predictions'][0]['outputs']


def build_query_encoder(problem, data_dir, embed_code=False):
  """Build a query encoder.

  Args:
    problem: The name of the T2T problem to use
    data_dir: Directory containing the data. This should include the vocabulary.
    embed_code: Whether to compute embeddings for natural language or code.
  """
  encoder = query.get_encoder(problem, data_dir)
  query_encoder = functools.partial(query.encode_query, encoder, embed_code)

  return query_encoder

def start_search_server(argv=None):
  """Start a Flask REST server.

  This routine starts a Flask server which maintains
  an in memory index and a reverse-lookup database of
  Python files which can be queried via a simple REST
  API. It also serves the UI for a friendlier interface.

  Args:
    argv: A list of strings representing command line arguments.
  """
  args = arguments.parse_arguments(argv)

  if not os.path.isdir(args.tmp_dir):
    os.makedirs(args.tmp_dir)

  logging.info('Reading %s', args.lookup_file)
  lookup_data = []
  with tf.gfile.Open(args.lookup_file) as lookup_file:
    reader = csv.reader(lookup_file)
    for row in reader:
      lookup_data.append(row)

  tmp_index_file = os.path.join(args.tmp_dir, os.path.basename(args.index_file))

  logging.info('Reading %s', args.index_file)
  if not os.path.isfile(tmp_index_file):
    tf.gfile.Copy(args.index_file, tmp_index_file)

  # Build an an encoder for the natural language strings.
  query_encoder = build_query_encoder(args.problem, args.data_dir,
                                      embed_code=False)
  embedding_fn = functools.partial(embed_query, query_encoder, args.serving_url)

  search_engine = CodeSearchEngine(tmp_index_file, lookup_data, embedding_fn)
  search_server = CodeSearchServer(search_engine, args.ui_dir, host=args.host, port=args.port)
  search_server.run()


if __name__ == '__main__':
  logging.basicConfig(level=logging.INFO,
                      format=('%(levelname)s|%(asctime)s'
                              '|%(pathname)s|%(lineno)d| %(message)s'),
                      datefmt='%Y-%m-%dT%H:%M:%S',
                      )
  logging.getLogger().setLevel(logging.INFO)
  start_search_server()
