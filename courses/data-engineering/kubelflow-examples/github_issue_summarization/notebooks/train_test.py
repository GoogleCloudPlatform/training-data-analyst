import os
import tempfile
import unittest

import train

class TrainTest(unittest.TestCase):

  def test_keras(self):
    """Test training_with_keras."""
    output_dir = tempfile.mkdtemp()
    output_model = os.path.join(output_dir, "model.h5")

    body_pp_dpkl = os.path.join(output_dir, "body_pp.dpkl")
    title_pp_dpkl = os.path.join(output_dir, "body_pp.dpkl")

    title_vecs = os.path.join(output_dir, "title.npy")
    body_vecs = os.path.join(output_dir, "body.npy")

    this_dir = os.path.dirname(__file__)
    args = [
      "--sample_size=100",
      "--num_epochs=1",
      "--input_data=" + os.path.join(this_dir, "test_data",
                                     "github_issues_sample.csv"),
      "--output_model=" + output_model,
      "--output_body_preprocessor_dpkl="+ body_pp_dpkl,
      "--output_title_preprocessor_dpkl="+ title_pp_dpkl,
      "--output_train_title_vecs_npy=" + title_vecs,
      "--output_train_body_vecs_npy=" + body_vecs,
    ]

    train.main(args)

    output_files = [
      output_model, body_pp_dpkl, title_pp_dpkl, title_vecs, body_vecs
    ]

    for f in output_files:
      self.assertTrue(os.path.exists(f))

  # TODO(https://github.com/kubeflow/examples/issues/280)
  # TODO(https://github.com/kubeflow/examples/issues/196)
  # This test won't work until we fix the code to work using the estimator
  # API.
  @unittest.skip("skip estimator test")
  def test_estimator(self):
    """Test training_with_keras."""
    output_dir = tempfile.mkdtemp()
    output_model = os.path.join(output_dir, "model")

    body_pp_dpkl = os.path.join(output_dir, "body_pp.dpkl")
    title_pp_dpkl = os.path.join(output_dir, "body_pp.dpkl")

    title_vecs = os.path.join(output_dir, "title.npy")
    body_vecs = os.path.join(output_dir, "body.npy")

    this_dir = os.path.dirname(__file__)
    args = [
      "--sample_size=100",
      "--num_epochs=1",
      "--input_data=" + os.path.join(this_dir, "test_data",
                                     "github_issues_sample.csv"),
      "--output_model=" + output_model,
      "--output_body_preprocessor_dpkl="+ body_pp_dpkl,
      "--output_title_preprocessor_dpkl="+ title_pp_dpkl,
      "--output_train_title_vecs_npy=" + title_vecs,
      "--output_train_body_vecs_npy=" + body_vecs,
      "--mode=estimator",
    ]

    train.main(args)

    output_files = [
      output_model, body_pp_dpkl, title_pp_dpkl, title_vecs, body_vecs
    ]

    for f in output_files:
      self.assertTrue(os.path.exists(f))

if __name__ == "__main__":
  unittest.main()
