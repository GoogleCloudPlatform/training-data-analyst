import os
import sys
import apache_beam.options.pipeline_options as pipeline_options


class PipelineCLIOptions(pipeline_options.StandardOptions,
                         pipeline_options.WorkerOptions,
                         pipeline_options.SetupOptions,
                         pipeline_options.GoogleCloudOptions):
  """A unified arguments parser.

  This parser directly exposes all the underlying Beam
  options available to the user (along with some custom
  arguments). To use, simply pass the arguments list as
  `PipelineCLIOptions(argv)`.

  Args:
    argv: A list of strings representing CLI options.
  """

  @classmethod
  def _add_argparse_args(cls, parser):
    add_parser_arguments(parser)


def add_parser_arguments(parser):
  additional_args_parser = parser.add_argument_group('Custom Arguments')
  additional_args_parser.add_argument('--target_dataset', metavar='', type=str,
                                      help='BigQuery dataset for output results')
  additional_args_parser.add_argument('--pre_transformed', action='store_true',
                      help='Use a pre-transformed BigQuery dataset')
  additional_args_parser.add_argument('--wait_until_finished', action='store_true',
                      help='Wait until preprocess job is finished')

  additional_args_parser.add_argument('--github_files', default='',
                    help=('If specified read the GitHub dataset '
                          'from the specified json files. Each line of text '
                          'should be a json record with two fields content and '
                          'repo_path'))

  additional_args_parser.add_argument('--github_table', default='',
                      help=('If specified read the entire GitHub dataset '
                            'specified as PROJECT:DATASET.TABLE. If not '
                            'specified we run a query to filter the data.'))
  additional_args_parser.add_argument('--failed_tokenize_table', metavar='', type=str,
                                   help='The BigQuery table containing the '
                                        'failed tokenize entry. This should be '
                                        'of the form PROJECT:DATASET.TABLE.')

  predict_args_parser = parser.add_argument_group('Batch Prediction Arguments')
  predict_args_parser.add_argument('--token_pairs_table', metavar='', type=str,
                                   help='The BigQuery table containing the '
                                        'token pairs. This should be '
                                        'of the form PROJECT:DATASET.TABLE.')
  predict_args_parser.add_argument('--function_embeddings_table', metavar='', type=str,
                                   help='The BigQuery table to write the '
                                        'function embeddings too. This should be '
                                        'of the form PROJECT:DATASET.TABLE.')
  predict_args_parser.add_argument('--problem', metavar='', type=str,
                                   help='Name of the T2T problem')
  predict_args_parser.add_argument('--data_dir', metavar='', type=str,
                                   help='Path to directory of the T2T problem data')
  predict_args_parser.add_argument('--saved_model_dir', metavar='', type=str,
                                   help='Path to directory containing Tensorflow SavedModel')
  predict_args_parser.add_argument('--output_dir', metavar='', type=str,
                                   help='Path to directory where the output '
                                        'should should be written.')

def prepare_pipeline_opts(argv=None):
  """Prepare pipeline options from CLI arguments.

  This uses the unified PipelineCLIOptions parser
  and adds modifications on top. It adds a `setup_file`
  to allow installation of dependencies on Dataflow workers.
  These implicit changes allow ease-of-use.

  Use `-h` CLI argument to see the list of all possible
  arguments.

  Args:
    argv: A list of strings representing the CLI arguments.

  Returns:
    A PipelineCLIOptions object whose `_visible_options`
    contains the parsed Namespace object.
  """
  argv = argv or sys.argv[1:]
  argv.extend([
    '--setup_file',
    os.path.abspath(os.path.join(__file__, '../../../../setup.py')),
  ])

  pipeline_opts = PipelineCLIOptions(flags=argv)

  return pipeline_opts
