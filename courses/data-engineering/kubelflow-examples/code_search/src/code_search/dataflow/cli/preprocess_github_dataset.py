import logging
import json

import apache_beam as beam
import code_search.dataflow.cli.arguments as arguments
import code_search.dataflow.transforms.github_bigquery as gh_bq
import code_search.dataflow.transforms.github_dataset as github_dataset
import code_search.dataflow.do_fns.dict_to_csv as dict_to_csv

class JsonCoder(object):
  """A JSON coder interpreting each line as a JSON string."""

  def encode(self, x): # pylint: disable=no-self-use
    return json.dumps(x)

  def decode(self, x): # pylint: disable=no-self-use
    return json.loads(x)

def preprocess_github_dataset(argv=None):
  """Apache Beam pipeline for pre-processing Github dataset.

  At a high level, this pipeline does the following things:
    - Read Github Python files from BigQuery
    - If Github Python files have already been processed, use the
      pre-processed table instead (using flag `--pre-transformed`)
    - Tokenize files into pairs of function definitions and docstrings
    - See `transforms.github_dataset.TransformGithubDataset` for details of tables created
    - Additionally, store pairs of docstring and function tokens in a CSV file
      for training

  NOTE: The number of output file shards have been fixed (at 100) to avoid a large
  number of output files, making it manageable.
  """
  pipeline_opts = arguments.prepare_pipeline_opts(argv)
  args = pipeline_opts._visible_options  # pylint: disable=protected-access

  pipeline = beam.Pipeline(options=pipeline_opts)

  if args.pre_transformed:
    token_pairs = (pipeline
      | "Read Transformed Github Dataset" >> gh_bq.ReadTransformedGithubDataset(
        args.project, dataset=args.target_dataset)
    )
  else:
    if args.github_files:
      logging.info("Will read the GitHub data from %s", args.github_files)
      input_records = (pipeline
            | "Read Github Dataset" >>  beam.io.ReadFromText(args.github_files,
                                                             coder=JsonCoder()))
    elif args.github_table:
      logging.info("Will read the entire table %s", args.github_table)
      source = beam.io.BigQuerySource(table=args.github_table)
      input_records = (pipeline
            | "Read Github Dataset" >> beam.io.Read(source))
    else:
      # Use only a query of the data.
      logging.info("Reading data using a query.")
      input_records = (pipeline
        | "Read Github Dataset" >> gh_bq.ReadGithubDataset(args.project))
    token_pairs = (input_records
      | "Transform Github Dataset" >> github_dataset.TransformGithubDataset(
                args.token_pairs_table, args.failed_tokenize_table)
    )

  (token_pairs  # pylint: disable=expression-not-assigned
    | "Format for CSV Write" >> beam.ParDo(dict_to_csv.DictToCSVString(
      ['docstring_tokens', 'function_tokens']))
    | "Write CSV" >> beam.io.WriteToText('{}/func-doc-pairs'.format(args.data_dir),
                                         file_name_suffix='.csv',
                                         num_shards=100)
  )

  result = pipeline.run()
  logging.info("Submitted Dataflow job: %s", result)
  if args.wait_until_finished:
    result.wait_until_finish()

  return result

if __name__ == '__main__':
  logging.basicConfig(level=logging.INFO,
                      format=('%(levelname)s|%(asctime)s'
                              '|%(pathname)s|%(lineno)d| %(message)s'),
                      datefmt='%Y-%m-%dT%H:%M:%S',
                      )
  logging.getLogger().setLevel(logging.INFO)
  preprocess_github_dataset()
