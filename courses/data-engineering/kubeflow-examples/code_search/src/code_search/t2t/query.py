import base64
import tensorflow as tf
from tensor2tensor.data_generators import text_encoder
from tensor2tensor.utils import registry


def get_encoder(problem_name, data_dir):
  """Get encoder from the T2T problem.This might
  vary by problem, keeping generic as a reference
  """
  problem = registry.problem(problem_name)
  hparams = tf.contrib.training.HParams(data_dir=data_dir)
  problem.get_hparams(hparams)
  return problem.feature_info["inputs"].encoder


def encode_query(encoder, embed_code, query_str):
  """Encode the input query string using encoder. This
  might vary by problem but keeping generic as a reference.
  Note that in T2T problems, the 'targets' key is needed
  even though it is ignored during inference.
  See tensorflow/tensor2tensor#868

  Args:
    encoder: Encoder to encode the string as a vector.
    embed_code: Bool determines whether to treat query_str as a natural language
      query and use the associated embedding for natural language or to
      treat it as code and use the associated embeddings.
    query_str: The data to compute embeddings for.
  """

  encoded_str = encoder.encode(query_str) + [text_encoder.EOS_ID]

  embed_code_value = 0
  if embed_code:
    embed_code_value = 1

  features = {
      "inputs": tf.train.Feature(int64_list=tf.train.Int64List(value=encoded_str)),
      "targets": tf.train.Feature(int64_list=tf.train.Int64List(value=[0])),
      # The embed code feature determines whether we treat the input (0)
      # or code (1). Since we want to compute the query embeddings we set it
      # to 0.
      "embed_code": tf.train.Feature(int64_list=tf.train.Int64List(
        value=[embed_code_value])),
  }
  example = tf.train.Example(features=tf.train.Features(feature=features))
  return base64.b64encode(example.SerializeToString()).decode('utf-8')

def decode_result(decoder, list_ids):
  return decoder.decode(list_ids)
