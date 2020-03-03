""" Module that sends a practical request to the tf-server.

Obtains the prediction for a given date in the test.
"""
import numpy as np

#pylint: disable=no-name-in-module
from helpers import preprocess
from . import request_helper #pylint: disable=relative-beyond-top-level


def send_pratical_request(date="2014-08-12"):
  """Obtain the prediction for a certain date in the test set.

  Args:
    date (str): request date to obtain prediction

  """
  # create input from request date
  tickers = ['snp', 'nyse', 'djia', 'nikkei', 'hangseng', 'ftse', 'dax', 'aord']
  closing_data = preprocess.load_data(tickers)
  index = closing_data.index.get_loc(date) - 7
  # because first 7 days are not accounted in the time series
  training_test_data = preprocess.preprocess_data(closing_data)
  input_tensor = np.expand_dims(
      training_test_data[training_test_data.columns[2:]].values[index],
      axis=0).astype(np.float32)

  request_helper.send_request(input_tensor)


send_pratical_request()
