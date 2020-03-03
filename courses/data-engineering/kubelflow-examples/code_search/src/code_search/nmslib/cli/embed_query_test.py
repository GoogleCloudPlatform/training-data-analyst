# coding=utf-8
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Test embedding query using TFServing.

This is a manual/E2E test that assumes TFServing is running externally
(e.g. Docker container or K8s pod).

The script start_test_server.sh can be used to start a Docker container
when running locally.

To run TFServing we need a model. start_test_server.sh will use a model
in ../../t2t/test_data/model

code_search must be a top level Python package.

 requires host machine has tensorflow_model_server executable available
"""

# TODO(jlewi): Starting the test seems very slow. I wonder if this is because
# tensor2tensor is loading a bunch of models and if maybe we can skip that.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import datetime
import logging
import os
import unittest
import tensorflow as tf

import numpy as np

from code_search.nmslib.cli  import start_search_server

start = datetime.datetime.now()

FLAGS = tf.flags.FLAGS

PROBLEM_NAME = "kf_github_function_docstring"

class TestEmbedQuery(unittest.TestCase):

  @unittest.skipIf(os.getenv("PROW_JOB_ID"), "Manual test not run on prow")
  def test_embed(self):
    """Test that we can embed the search query string via tf.serving.

    This test assumes the model is running as an external process in TensorFlow
    serving.

    The external process can be started a variety of ways e.g. subprocess,
    kubernetes, or docker container.

    The script start_test_server.sh can be used to start TFServing in
    docker container.
    """
    # Directory containing the vocabulary.
    test_data_dir = os.path.abspath(
      os.path.join(os.path.dirname(__file__), "..", "..", "t2t", "test_data"))
    # 8501 should be REST port
    server = os.getenv("TEST_SERVER", "localhost:8501")

    # Model name matches the subdirectory in TF Serving's model Directory
    # containing models.
    model_name = "test_model_20181031"
    serving_url = "http://{0}/v1/models/{1}:predict".format(server, model_name)
    query = "Write to GCS"
    query_encoder = start_search_server.build_query_encoder(PROBLEM_NAME,
                                                            test_data_dir)
    code_encoder = start_search_server.build_query_encoder(PROBLEM_NAME,
                                                           test_data_dir,
                                                           embed_code=True)

    query_result = start_search_server.embed_query(query_encoder, serving_url, query)
    code_result = start_search_server.embed_query(code_encoder, serving_url, query)

    # As a sanity check ensure the vectors aren't equal
    q_vec = np.array(query_result)
    q_vec = q_vec/np.sqrt(np.dot(q_vec, q_vec))
    c_vec = np.array(code_result)
    c_vec = c_vec/np.sqrt(np.dot(c_vec, c_vec))

    dist = np.dot(q_vec, c_vec)
    self.assertNotAlmostEqual(1, dist)
    logging.info("Done")

if __name__ == "__main__":
  logging.getLogger().setLevel(logging.INFO)
  unittest.main()
