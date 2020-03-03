"""Beam DoFns specific to `code_search.dataflow.transforms.github_dataset`."""

import logging
import apache_beam as beam
from apache_beam import pvalue
import code_search.dataflow.utils as utils

class SplitRepoPath(beam.DoFn):
  """Update element keys to separate repo path and file path.

  This DoFn's only purpose is to be used after
  `code_search.dataflow.transforms.github_bigquery.ReadGithubDataset`
  to split the source dictionary key into two target keys.
  """

  @property
  def source_key(self):
    return u'repo_path'

  @property
  def target_keys(self):
    return [u'nwo', u'path']

  def process(self, element, *_args, **_kwargs):
    """Process Python file attributes.

    This simple DoFn splits the `repo_path` into
    independent properties of owner (`nwo`) and
    relative file path (`path`). This value is
    space-delimited and split over the first space
    is enough.

    Args:
      element: A Python dict of the form,
        {
          "repo_path": "STRING",
          "content": "STRING",
        }

    Yields:
      An updated Python dict of the form,
        {
          "nwo": "STRING",
          "path": "STRING",
          "content": "STRING",
        }
    """
    values = element.pop(self.source_key).split(' ', 1)

    for key, value in zip(self.target_keys, values):
      element[key] = value

    yield element


class TokenizeFunctionDocstrings(beam.DoFn):
  """Tokenize function and docstrings.

  This DoFn takes in the rows from BigQuery and tokenizes
  the file content present in the content key. This
  yields an updated dictionary with the new tokenized
  data in the pairs key.
  """

  @property
  def content_key(self):
    return 'content'

  @property
  def info_keys(self):
    return [
      u'function_name',
      u'lineno',
      u'original_function',
      u'function_tokens',
      u'docstring_tokens',
    ]

  def process(self, element, *_args, **_kwargs):
    """Get list of Function-Docstring tokens

    This processes each Python file's content
    and returns a list of metadata for each extracted
    pair. These contain the tokenized functions and
    docstrings. In cases where the tokenization fails,
    a side output is returned. All values are unicode
    for serialization.

    Args:
      element: A Python dict of the form,
        {
          "nwo": "STRING",
          "path": "STRING",
          "content": "STRING",
        }

    Yields:
      A Python list of the form,
      [
        {
          "nwo": "STRING",
          "path": "STRING",
          "function_name": "STRING",
          "lineno": "STRING",
          "original_function": "STRING",
          "function_tokens": "STRING",
          "docstring_tokens": "STRING",
        },
        ...
      ]
    """
    try:
      content_blob = element.pop(self.content_key)
      pairs = utils.get_function_docstring_pairs(content_blob)

      result = [
        dict(zip(self.info_keys, pair_tuple), **element)
        for pair_tuple in pairs
      ]

      yield result
    # TODO(jlewi): Can we narrow down the scope covered by swallowing
    # errors? It should really only be the AST parsing code so can
    # we move try/catch into get_function_docstring_pairs?
    except Exception as e:  # pylint: disable=broad-except
      logging.warning('Tokenization failed, %s', e.message)
      yield pvalue.TaggedOutput('err', element)
