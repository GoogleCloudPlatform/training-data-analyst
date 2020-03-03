import argparse
import os


def add_common_arguments(parser):
  parser.add_argument('--data_dir', type=str, metavar='',
                     help='Path to directory with CSV files containing function embeddings')
  parser.add_argument('--lookup_file', type=str, metavar='',
                     help='Path to CSV file for reverse index lookup.')
  parser.add_argument('--index_file', type=str, metavar='',
                     help='Path to output index file')
  parser.add_argument('--tmp_dir', type=str, metavar='', default='/tmp/code_search',
                     help='Path to temporary data directory')


def add_server_arguments(parser):
  parser.add_argument('--problem', type=str, metavar='',
                      help='Name of the T2T problem')
  parser.add_argument('--serving_url', type=str, metavar='',
                      help='Complete URL to TF Serving Inference server')
  parser.add_argument('--host', type=str, metavar='', default='0.0.0.0',
                     help='Host to start server on')
  parser.add_argument('--port', type=int, metavar='', default=8008,
                     help='Port to bind server to')
  parser.add_argument('--ui_dir', type=int, metavar='',
                     help='Path to static assets for the UI')


def parse_arguments(argv=None):
  parser = argparse.ArgumentParser(prog='Code Search Index Server')

  add_common_arguments(parser)

  server_args_parser = parser.add_argument_group('Server Arguments')
  add_server_arguments(server_args_parser)

  args = parser.parse_args(argv)
  args.data_dir = os.path.expanduser(args.data_dir)
  args.lookup_file = os.path.expanduser(args.lookup_file)
  args.index_file = os.path.expanduser(args.index_file)
  args.tmp_dir = os.path.expanduser(args.tmp_dir)

  args.ui_dir = os.path.abspath(os.path.join(__file__, '../../../../ui/build'))

  return args
