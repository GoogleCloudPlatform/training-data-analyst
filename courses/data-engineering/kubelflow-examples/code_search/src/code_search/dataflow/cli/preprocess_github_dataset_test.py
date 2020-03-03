import glob
import logging
import unittest
import os
import tempfile

from code_search.dataflow.cli import preprocess_github_dataset

class TestPreprocess(unittest.TestCase):
  def test_e2e(self):
    data_dir = os.path.join(
      os.path.dirname(__file__), "test_data")
    data_file = os.path.join(data_dir, "sample.json")

    out_dir = tempfile.mkdtemp()
    logging.info("Using out directory: %s", out_dir)
    result = preprocess_github_dataset.preprocess_github_dataset(
      ["--github_files=" + data_file,
       "--data_dir=" + out_dir])

    result.wait_until_finish()

    num_output_shards = 0
    num_output = 0
    for f in glob.glob(os.path.join(out_dir, "*.csv")):
      num_output_shards += 1
      with open(f) as hf:
        lines = hf.readlines()
        num_output += len(lines)

    self.assertGreater(num_output_shards, 0)
    self.assertGreater(num_output, 0)
    logging.info("Done")

if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO,
                      format=('%(levelname)s|%(asctime)s'
                              '|%(pathname)s|%(lineno)d| %(message)s'),
                      datefmt='%Y-%m-%dT%H:%M:%S',
                      )
  logging.getLogger().setLevel(logging.INFO)
  unittest.main()
