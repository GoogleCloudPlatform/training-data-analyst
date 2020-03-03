"""Module that preprocesses the data needed for the machine learning model.

Downloads and preprocesses stock data obtained from Public Google BigQuery tables.
"""
from google.cloud import bigquery #pylint: disable=no-name-in-module
import numpy as np
import pandas as pd


def load_data(tickers, year_cutoff=None):
  """Load stock market data (close values for each day) for given tickers.

  Args:
    tickers (list): list of tickers

  Returns:
    pandas.dataframe: dataframe with close values of tickers

  """
  # instantiate bigquery client
  bigquery_client = bigquery.Client()

  # get the data
  bq_query = {}
  for ticker in tickers:
    query = 'SELECT Date, Close from `bingo-ml-1.market_data.{}`'.format(ticker)
    if year_cutoff:
      query += 'WHERE EXTRACT(YEAR FROM Date) >= {}'.format(year_cutoff)
    bq_query[ticker] = bigquery_client.query(query)

  results = {}
  for ticker in tickers:
    results[ticker] = bq_query[ticker].result().to_dataframe().set_index('Date')

  # sort and fill blanks
  closing_data = pd.DataFrame()
  for ticker in tickers:
    closing_data['{}_close'.format(ticker)] = results[ticker]['Close']
  closing_data.sort_index(inplace=True)
  closing_data = closing_data.fillna(method='ffill')

  return closing_data


def preprocess_data(closing_data):
  """Preprocesses data into time series.

  Args:
    closing_data (pandas.dataframe):  dataframe with close values of tickers

  Returns:
    pandas.dataframe: dataframe with time series

  """
  # transform into log return
  log_return_data = pd.DataFrame()
  tickers = [column_header.split("_")[0] for column_header in closing_data.columns.values]
  for ticker in tickers:
    log_return_data['{}_log_return'.format(ticker)] = np.log(
        closing_data['{}_close'.format(ticker)] /
        closing_data['{}_close'.format(ticker)].shift())

  log_return_data['snp_log_return_positive'] = 0
  log_return_data.ix[log_return_data['snp_log_return'] >= 0, 'snp_log_return_positive'] = 1
  log_return_data['snp_log_return_negative'] = 0
  log_return_data.ix[log_return_data['snp_log_return'] < 0, 'snp_log_return_negative'] = 1

  # create dataframe
  training_test_data = pd.DataFrame(
      columns=[
          'snp_log_return_positive', 'snp_log_return_negative',
          'snp_log_return_1', 'snp_log_return_2', 'snp_log_return_3',
          'nyse_log_return_1', 'nyse_log_return_2', 'nyse_log_return_3',
          'djia_log_return_1', 'djia_log_return_2', 'djia_log_return_3',
          'nikkei_log_return_0', 'nikkei_log_return_1', 'nikkei_log_return_2',
          'hangseng_log_return_0', 'hangseng_log_return_1', 'hangseng_log_return_2',
          'ftse_log_return_0', 'ftse_log_return_1', 'ftse_log_return_2',
          'dax_log_return_0', 'dax_log_return_1', 'dax_log_return_2',
          'aord_log_return_0', 'aord_log_return_1', 'aord_log_return_2'])

  # fill dataframe with time series
  for i in range(7, len(log_return_data)):
    training_test_data = training_test_data.append(
      {'snp_log_return_positive': log_return_data['snp_log_return_positive'].ix[i],
       'snp_log_return_negative': log_return_data['snp_log_return_negative'].ix[i],
       'snp_log_return_1': log_return_data['snp_log_return'].ix[i - 1],
       'snp_log_return_2': log_return_data['snp_log_return'].ix[i - 2],
       'snp_log_return_3': log_return_data['snp_log_return'].ix[i - 3],
       'nyse_log_return_1': log_return_data['nyse_log_return'].ix[i - 1],
       'nyse_log_return_2': log_return_data['nyse_log_return'].ix[i - 2],
       'nyse_log_return_3': log_return_data['nyse_log_return'].ix[i - 3],
       'djia_log_return_1': log_return_data['djia_log_return'].ix[i - 1],
       'djia_log_return_2': log_return_data['djia_log_return'].ix[i - 2],
       'djia_log_return_3': log_return_data['djia_log_return'].ix[i - 3],
       'nikkei_log_return_0': log_return_data['nikkei_log_return'].ix[i],
       'nikkei_log_return_1': log_return_data['nikkei_log_return'].ix[i - 1],
       'nikkei_log_return_2': log_return_data['nikkei_log_return'].ix[i - 2],
       'hangseng_log_return_0': log_return_data['hangseng_log_return'].ix[i],
       'hangseng_log_return_1': log_return_data['hangseng_log_return'].ix[i - 1],
       'hangseng_log_return_2': log_return_data['hangseng_log_return'].ix[i - 2],
       'ftse_log_return_0': log_return_data['ftse_log_return'].ix[i],
       'ftse_log_return_1': log_return_data['ftse_log_return'].ix[i - 1],
       'ftse_log_return_2': log_return_data['ftse_log_return'].ix[i - 2],
       'dax_log_return_0': log_return_data['dax_log_return'].ix[i],
       'dax_log_return_1': log_return_data['dax_log_return'].ix[i - 1],
       'dax_log_return_2': log_return_data['dax_log_return'].ix[i - 2],
       'aord_log_return_0': log_return_data['aord_log_return'].ix[i],
       'aord_log_return_1': log_return_data['aord_log_return'].ix[i - 1],
       'aord_log_return_2': log_return_data['aord_log_return'].ix[i - 2]},
      ignore_index=True)

  return training_test_data


def train_test_split(training_test_data, train_test_ratio=0.8):
  """Splits the data into a training and test set according to the provided ratio.

  Args:
    training_test_data (pandas.dataframe): dict with time series
    train_test_ratio (float): ratio of train test split

  Returns:
    tensors: predictors and classes tensors for training and respectively test set

  """
  predictors_tf = training_test_data[training_test_data.columns[2:]]
  classes_tf = training_test_data[training_test_data.columns[:2]]

  training_set_size = int(len(training_test_data) * train_test_ratio)

  train_test_dict = {'training_predictors_tf': predictors_tf[:training_set_size],
                     'training_classes_tf': classes_tf[:training_set_size],
                     'test_predictors_tf': predictors_tf[training_set_size:],
                     'test_classes_tf': classes_tf[training_set_size:]}

  return train_test_dict
