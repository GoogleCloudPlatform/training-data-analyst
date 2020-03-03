from tensor2tensor.utils import registry
from .function_docstring import GithubFunctionDocstring


@registry.register_problem('cs_github_function_docstring')
class GithubFunctionDocstringExtended(GithubFunctionDocstring):
  """Function Docstring problem with extended semantics.

  This problem keeps all the properties of the original,
  with one change - the semantics of `data_dir` now dictate that
  the raw CSV files containing the function docstring pairs should
  already be available in the `data_dir`. This allows for the user
  to modify the `data_dir` to point to a new set of data points when
  needed and train an updated model.

  As a reminder, in the standard setting, `data_dir` is only meant
  to be the output directory for TFRecords of an immutable dataset
  elsewhere (more particularly at `self.DATA_PATH_PREFIX`).
  """

  def get_csv_files(self, _data_dir, tmp_dir, _dataset_split):
    self.DATA_PATH_PREFIX = _data_dir
    return super(GithubFunctionDocstringExtended,
                 self).get_csv_files(_data_dir, tmp_dir, _dataset_split)
