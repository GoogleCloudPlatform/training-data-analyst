"""Beam DoFns specific to `code_search.dataflow.transforms.function_embeddings`."""

import apache_beam as beam

from code_search.t2t.query import get_encoder, encode_query


class EncodeFunctionTokens(beam.DoFn):
  """Encode function tokens.

  This DoFn prepares the function tokens for
  inference by a SavedModel estimator downstream.

  Args:
    problem: A string representing the registered Tensor2Tensor Problem.
    data_dir: A string representing the path to data directory.
  """
  def __init__(self, problem, data_dir):
    super(EncodeFunctionTokens, self).__init__()

    self.problem = problem
    self.data_dir = data_dir

  @property
  def function_tokens_key(self):
    return u'function_tokens'

  @property
  def instances_key(self):
    return u'instances'

  def process(self, element, *_args, **_kwargs):
    """Encode the function instance.

    This DoFn takes a tokenized function string and
    encodes them into a base64 string of TFExample
    binary format. The "function_tokens" are encoded
    and stored into the "instances" key in a format
    ready for consumption by TensorFlow SavedModel
    estimators. The encoder is provided by a
    Tensor2Tensor problem as provided in the constructor.

    Args:
      element: A Python dict of the form,
        {
          "nwo": "STRING",
          "path": "STRING",
          "function_name": "STRING",
          "lineno": "STRING",
          "original_function": "STRING",
          "function_tokens": "STRING",
          "docstring_tokens": "STRING",
        }

    Yields:
      An updated Python dict of the form
        {
          "nwo": "STRING",
          "path": "STRING",
          "function_name": "STRING",
          "lineno": "STRING",
          "original_function": "STRING",
          "function_tokens": "STRING",
          "docstring_tokens": "STRING",
          "instances": [
            {
              "input": {
                "b64": "STRING",
              }
            }
          ]
        }
    """
    encoder = get_encoder(self.problem, self.data_dir)
    encoded_function = encode_query(encoder, True,
                                    element.get(self.function_tokens_key))

    element[self.instances_key] = [{'input': {'b64': encoded_function}}]
    yield element


class ProcessFunctionEmbedding(beam.DoFn):
  """Process results from PredictionDoFn.

  This is a DoFn for post-processing on inference
  results from a SavedModel estimator which are
  returned by the PredictionDoFn.
  """

  @property
  def function_embedding_key(self):
    return 'function_embedding'

  @property
  def predictions_key(self):
    return 'predictions'

  @property
  def pop_keys(self):
    return [
      'predictions',
      'docstring_tokens',
      'function_tokens',
      'instances',
    ]

  def process(self, element, *_args, **_kwargs):
    """Post-Process Function embedding.

    This converts the incoming function instance
    embedding into a serializable string for downstream
    tasks. It also pops any extraneous keys which are
    no more required. The "lineno" key is also converted
    to a string for serializability downstream.

    Args:
      element: A Python dict of the form,
        {
          "nwo": "STRING",
          "path": "STRING",
          "function_name": "STRING",
          "lineno": "STRING",
          "original_function": "STRING",
          "function_tokens": "STRING",
          "docstring_tokens": "STRING",
          "instances": [
            {
              "input": {
                "b64": "STRING",
              }
            }
          ],
          "predictions": [
            {
              "outputs": [
                FLOAT,
                FLOAT,
                ...
              ]
            }
          ],
        }

    Yields:
      An update Python dict of the form,
        {
          "nwo": "STRING",
          "path": "STRING",
          "function_name": "STRING",
          "lineno": "STRING",
          "original_function": "STRING",
          "function_embedding": "STRING",
        }
    """
    prediction = element.get(self.predictions_key)[0]['outputs']
    element[self.function_embedding_key] = ','.join([
      str(val).decode('utf-8') for val in prediction
    ])

    element['lineno'] = str(element['lineno']).decode('utf-8')

    for key in self.pop_keys:
      element.pop(key)

    yield element
