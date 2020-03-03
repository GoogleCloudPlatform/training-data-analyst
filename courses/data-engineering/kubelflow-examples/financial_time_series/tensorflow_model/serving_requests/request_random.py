""" Module that sends a random request to the tf-server.

Uses numpy random array to obtain a response/prediction from the tf-server.
"""

import numpy as np

from . import request_helper   #pylint: disable=relative-beyond-top-level


def send_random_request():
  """Obtain the prediction for a random request (test function for the tf-server)."""
  # create random input
  input_tensor = np.random.rand(1, 24).astype(np.float32)
  # send request
  request_helper.send_request(input_tensor)

send_random_request()
