"""Github function/text similatrity problems."""
import csv
import logging
from six import StringIO
from tensor2tensor.data_generators import generator_utils
from tensor2tensor.data_generators import text_problems
from tensor2tensor.utils import metrics
from tensor2tensor.utils import registry
import tensorflow as tf

# There is a copy of the problem in the Tensor2Tensor library.
# http://bit.ly/2Olf34u
#
# We want to register this problem with a different name to make sure
# we don't end up using that problem.
# So we register it with the name kf
@registry.register_problem("kf_github_function_docstring")
class GithubFunctionDocstring(text_problems.Text2TextProblem):
  """Function and Docstring similarity Problem.

  This problem contains the data consisting of function
  and docstring pairs as CSV files. The files are structured
  such that they contain two columns without headers containing
  the docstring tokens and function tokens. The delimiter is
  ",".
  """

  DATA_PATH_PREFIX = "gs://kubeflow-examples/t2t-code-search/raw_data"
  NUM_SHARDS = 100

  @property
  def pair_files_list(self):
    """Return URL and file names.

    This format is a convention across the Tensor2Tensor (T2T)
    codebase. It should be noted that the file names are currently
    hardcoded. This is to preserve the semantics of a T2T problem.
    In case a change of these values is desired, one must subclass
    and override this property.

    # TODO(sanyamkapoor): Manually separate train/eval data set.

    Returns:
      A list of the format,
        [
          [
            "STRING",
            ("STRING", "STRING", ...)
          ],
          ...
        ]
      Each element is a list of size 2 where the first represents
      the source URL and the next is an n-tuple of file names.

      In this case, the tuple is of size 1 because the URL points
      to a file itself.
    """
    logging.info("Using %s shards", self.NUM_SHARDS)
    return [
        [
            "{}/func-doc-pairs-{:05}-of-{:05}.csv".format(
                self.DATA_PATH_PREFIX, i, self.NUM_SHARDS),
            ("func-doc-pairs-{:05}-of-{:05}.csv".format(i, self.NUM_SHARDS),)
        ]
        for i in range(self.NUM_SHARDS)
    ]

  @property
  def is_generate_per_split(self):
    return False

  @property
  def approx_vocab_size(self):
    return 2**13

  @property
  def max_samples_for_vocab(self):
    # FIXME(sanyamkapoor): This exists to handle memory explosion.
    return int(2e5)

  def get_csv_files(self, _data_dir, tmp_dir, _dataset_split):
    return [
        generator_utils.maybe_download(tmp_dir, file_list[0], uri)
        for uri, file_list in self.pair_files_list
    ]

  def generate_samples(self, data_dir, tmp_dir, dataset_split):
    """A generator to return data samples.Returns the data generator to return.


    Args:
      data_dir: A string representing the data directory.
      tmp_dir: A string representing the temporary directory and is
              used to download files if not already available.
      dataset_split: Train, Test or Eval.

    Yields:
      Each element yielded is of a Python dict of the form
        {"inputs": "STRING", "targets": "STRING", "embed_code": [0]}
    """
    csv_files = self.get_csv_files(data_dir, tmp_dir, dataset_split)

    for pairs_file in csv_files:
      tf.logging.debug("Reading {}".format(pairs_file))
      with tf.gfile.Open(pairs_file) as csv_file:
        for line in csv_file:
          reader = csv.reader(StringIO(line))
          for docstring_tokens, function_tokens in reader:
            yield {
                "inputs": docstring_tokens,
                "targets": function_tokens,
                "embed_code": [0],
            }

  def example_reading_spec(self):
    data_fields, data_items_to_decoders = super(GithubFunctionDocstring,
                                                self).example_reading_spec()
    data_fields["embed_code"] = tf.FixedLenFeature([1], dtype=tf.int64)
    return data_fields, data_items_to_decoders

  def eval_metrics(self):  # pylint: disable=no-self-use
    return [
        metrics.Metrics.ACC
    ]
