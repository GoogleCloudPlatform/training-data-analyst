import apache_beam as beam

import code_search.dataflow.do_fns.prediction_do_fn as pred
import code_search.dataflow.do_fns.function_embeddings as func_embeddings # pylint: disable=no-name-in-module


class FunctionEmbeddings(beam.PTransform):
  """Batch Prediction for Github dataset.

  This Beam pipeline takes in the transformed dataset,
  prepares each element's function tokens for prediction
  by encoding it into base64 format and returns an updated
  dictionary element with the embedding for further processing.

  Args:
    project: The project
    target_table: The table to write to. Should be of the form
      "project:dataset.table"
  """

  def __init__(self, problem, data_dir, saved_model_dir):
    super(FunctionEmbeddings, self).__init__()

    self.problem = problem
    self.data_dir = data_dir
    self.saved_model_dir = saved_model_dir

  def expand(self, input_or_inputs):
    batch_predict = (input_or_inputs
      | "Encoded Function Tokens" >> beam.ParDo(func_embeddings.EncodeFunctionTokens(
        self.problem, self.data_dir))
      | "Compute Function Embeddings" >> beam.ParDo(pred.PredictionDoFn(),
                                                    self.saved_model_dir).with_outputs('err',
                                                                                       main='main')
    )

    predictions = batch_predict.main

    formatted_predictions = (predictions
      | "Process Function Embeddings" >> beam.ParDo(func_embeddings.ProcessFunctionEmbedding())
    )

    return formatted_predictions
