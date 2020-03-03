"""Dataflow job to compute function embeddings."""
import logging

import apache_beam as beam

import code_search.dataflow.cli.arguments as arguments
from code_search.dataflow.transforms import bigquery
import code_search.dataflow.transforms.github_bigquery as gh_bq
import code_search.dataflow.transforms.github_dataset as github_dataset
import code_search.dataflow.transforms.function_embeddings as func_embed
import code_search.dataflow.do_fns.dict_to_csv as dict_to_csv


def create_function_embeddings(argv=None):
  """Creates Batch Prediction Pipeline using trained model.

  At a high level, this pipeline does the following things:
    - Read the Processed Github Dataset from BigQuery
    - Encode the functions using T2T problem
    - Get function embeddings using `kubeflow_batch_predict.dataflow.batch_prediction`
    - All results are stored in a BigQuery dataset (`args.function_embeddings_table`)
    - See `transforms.github_dataset.GithubBatchPredict` for details of tables created
    - Additionally, store CSV of docstring, original functions and other metadata for
      reverse index lookup during search engine queries.

  NOTE: The number of output file shards have been fixed (at 100) to avoid a large
  number of output files, making it manageable.
  """
  pipeline_opts = arguments.prepare_pipeline_opts(argv)
  args = pipeline_opts._visible_options  # pylint: disable=protected-access

  pipeline = beam.Pipeline(options=pipeline_opts)

  if args.token_pairs_table:
    token_pairs_query = gh_bq.ReadTransformedGithubDatasetQuery(
      args.token_pairs_table)
    token_pairs_source = beam.io.BigQuerySource(
      query=token_pairs_query.query_string, use_standard_sql=True)
    token_pairs = (pipeline
      | "Read Transformed Github Dataset" >> beam.io.Read(token_pairs_source)
    )
  else:
    token_pairs = (pipeline
      | "Read Github Dataset" >> gh_bq.ReadGithubDataset(args.project)
      | "Transform Github Dataset" >> github_dataset.TransformGithubDataset(None, None)
    )

  embeddings = (token_pairs
    | "Compute Function Embeddings" >> func_embed.FunctionEmbeddings(args.problem,
                                                                     args.data_dir,
                                                                     args.saved_model_dir)
  )

  function_embeddings_schema = bigquery.BigQuerySchema([
      ('nwo', 'STRING'),
      ('path', 'STRING'),
      ('function_name', 'STRING'),
      ('lineno', 'STRING'),
      ('original_function', 'STRING'),
      ('function_embedding', 'STRING')
    ])

  (embeddings  # pylint: disable=expression-not-assigned
    | "Save Function Embeddings" >>
       beam.io.WriteToBigQuery(table=args.function_embeddings_table,
                               schema=function_embeddings_schema.table_schema,
                               create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
                               write_disposition=beam.io.BigQueryDisposition.WRITE_EMPTY)
  )

  (embeddings  # pylint: disable=expression-not-assigned
    | "Format for Embeddings CSV Write" >> beam.ParDo(dict_to_csv.DictToCSVString(
        ['nwo', 'path', 'function_name', 'lineno', 'original_function', 'function_embedding']))
    | "Write Embeddings to CSV" >> beam.io.WriteToText('{}/func-index'.format(args.output_dir),
                                                       file_name_suffix='.csv',
                                                       num_shards=100)
  )

  result = pipeline.run()
  logging.info("Submitted Dataflow job: %s", result)
  # TODO(jlewi): Doesn't dataflow define a default option.
  if args.wait_until_finished:
    result.wait_until_finish()


if __name__ == '__main__':
  logging.basicConfig(level=logging.INFO,
                      format=('%(levelname)s|%(asctime)s'
                              '|%(pathname)s|%(lineno)d| %(message)s'),
                      datefmt='%Y-%m-%dT%H:%M:%S',
                      )
  logging.getLogger().setLevel(logging.INFO)
  create_function_embeddings()
