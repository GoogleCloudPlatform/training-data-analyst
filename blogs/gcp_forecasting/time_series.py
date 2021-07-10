"""Utilities for disa time-series modeling."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys

import numpy as np
import pandas as pd

from pandas.tseries.holiday import USFederalHolidayCalendar as calendar


def _keep(window, windows):
  """Helper function for creating rolling windows."""
  windows.append(window.copy())
  return -1.  # Float return value required for Pandas apply.


def create_rolling_features_label(series, window_size, pred_offset, pred_n=1):
  """Computes rolling window of the series and creates rolling window of label.

  Args:
    series: A Pandas Series. The indices are datetimes and the values are
      numeric type.
    window_size: integer; steps of historical data to use for features.
    pred_offset: integer; steps into the future for prediction.
    pred_n: integer; window size of label.

  Returns:
    Pandas dataframe where the index is the datetime predicting at. The columns
    beginning with "-" indicate windows N steps before the prediction time.

  Examples:
    >>> series = pd.Series(np.random.random(6),
                   index=pd.date_range(start='1/1/2018', end='1/06/2018'))
    # Example #1:
    >>> series
    2018-01-01    0.803948
    2018-01-02    0.269849
    2018-01-03    0.971984
    2018-01-04    0.809718
    2018-01-05    0.324454
    2018-01-06    0.229447
    >>> window_size = 3 # get 3 months of historical data
    >>> pred_offset = 1 # predict starting next month
    >>> pred_n = 1 # for predicting a single month
    >>> utils.create_rolling_features_label(series,
                                            window_size,
                                            pred_offset,
                                            pred_n)
    pred_datetime -3_steps      -2_steps        -1_steps        label
    2018-01-04    0.803948      0.269849        0.971984        0.809718
    2018-01-05    0.269849      0.971984        0.809718        0.324454
    2018-01-06    0.971984      0.809718        0.324454        0.229447

    # Example #2:
    >>> window_size = 3 # get 3 months of historical data
    >>> pred_offset = 2 # predict starting 2 months into future
    >>> pred_n = 1 # for predicting a single month
    >>> utils.create_rolling_features_label(series,
                                            window_size,
                                            pred_offset,
                                            pred_n)
    pred_datetime       -4_steps        -3_steps        -2_steps        label
    2018-01-05    0.803948      0.269849        0.971984        0.324454
    2018-01-06    0.269849      0.971984        0.809718        0.229447

    # Example #3:
    >>> window_size = 3 # get 3 months of historical data
    >>> pred_offset = 1 # predict starting next month
    >>> pred_n = 2 # for predicting a multiple months
    >>> utils.create_rolling_features_label(series,
                                            window_size,
                                            pred_offset,
                                            pred_n)
    pred_datetime -3_steps      -2_steps        -1_steps        label_0_steps
    label_1_steps
    2018-01-04    0.803948      0.269849        0.971984        0.809718
    0.324454
    2018-01-05    0.269849      0.971984        0.809718        0.324454
    0.229447
  """
  if series.isnull().sum() > 0:
    raise ValueError('Series must not contain missing values.')
  if pred_n < 1:
    raise ValueError('pred_n must not be < 1.')
  if len(series) < (window_size + pred_offset + pred_n):
    raise ValueError('window_size + pred_offset + pred_n must not be greater '
                     'than series length.')
  total_steps = len(series)

  def compute_rolling_window(series, window_size):
    # Accumulate series into list.
    windows = []
    series.rolling(window_size)\
      .apply(_keep, args=(windows,))
    return np.array(windows)

  features_start = 0
  features_end = total_steps - (pred_offset - 1) - pred_n
  historical_windows = compute_rolling_window(
      series[features_start:features_end], window_size)
  # Get label pred_offset steps into the future.
  label_start, label_end = window_size + pred_offset - 1, total_steps
  label_series = series[label_start:label_end]
  y = compute_rolling_window(label_series, pred_n)
  if pred_n == 1:
    # TODO(crawles): remove this if statement/label name. It's for backwards
    # compatibility.
    columns = ['label']
  else:
    columns = ['label_{}_steps'.format(i) for i in range(pred_n)]
  # Make dataframe. Combine features and labels.
  label_ix = label_series.index[0:len(label_series) + 1 - pred_n]
  df = pd.DataFrame(y, columns=columns, index=label_ix)
  df.index.name = 'pred_date'
  # Populate dataframe with past sales.
  for day in range(window_size - 1, -1, -1):
    day_rel_label = pred_offset + window_size - day - 1
    df.insert(0, '-{}_steps'.format(day_rel_label), historical_windows[:, day])
  return df


def add_aggregate_features(df, time_series_col_names):
  """Compute summary statistic features for every row of dataframe."""
  x = df[time_series_col_names]
  features = {}
  features['mean'] = x.mean(axis=1)
  features['std'] = x.std(axis=1)
  features['min'] = x.min(axis=1)
  features['max'] = x.max(axis=1)
  percentiles = range(10, 100, 20)
  for p in percentiles:
    features['{}_per'.format(p)] = np.percentile(x, p, axis=1)
  df_features = pd.DataFrame(features, index=x.index)
  return df_features.merge(df, left_index=True, right_index=True)


def move_column_to_end(df, column_name):
  temp = df[column_name]
  df.drop(column_name, axis=1, inplace=True)
  df[column_name] = temp


def is_between_dates(dates, start=None, end=None):
  """Return boolean indices indicating if dates occurs between start and end."""
  if start is None:
    start = pd.to_datetime(0)
  if end is None:
    end = pd.to_datetime(sys.maxsize)
  date_series = pd.Series(pd.to_datetime(dates))
  return date_series.between(start, end).values


def _count_holidays(dates, months, weeks):
  """Count number of holidays spanned in prediction windows."""
  cal = calendar()
  holidays = cal.holidays(start=dates.min(), end=dates.max())

  def count_holidays_during_month(date):
    n_holidays = 0
    beg = date
    end = date + pd.DateOffset(months=months, weeks=weeks)
    for h in holidays:
      if beg <= h < end:
        n_holidays += 1
    return n_holidays

  return pd.Series(dates).apply(count_holidays_during_month)


def _get_day_of_month(x):
  """From a datetime object, extract day of month."""
  return int(x.strftime('%d'))


def add_date_features(df, dates, months, weeks, inplace=False):
  """Create features using date that is being predicted on."""
  if not inplace:
    df = df.copy()
  df['doy'] = dates.dayofyear
  df['dom'] = dates.map(_get_day_of_month)
  df['month'] = dates.month
  df['year'] = dates.year
  df['n_holidays'] = _count_holidays(dates, months, weeks).values
  return df


class Metrics(object):
  """Performance metrics for regressor."""

  def __init__(self, y_true, predictions):
    self.y_true = y_true
    self.predictions = predictions
    self.residuals = self.y_true - self.predictions
    self.rmse = self.calculate_rmse(self.residuals)
    self.mae = self.calculate_mae(self.residuals)
    self.malr = self.calculate_malr(self.y_true, self.predictions)

  def calculate_rmse(self, residuals):
    """Root mean squared error."""
    return np.sqrt(np.mean(np.square(residuals)))

  def calculate_mae(self, residuals):
    """Mean absolute error."""
    return np.mean(np.abs(residuals))

  def calculate_malr(self, y_true, predictions):
    """Mean absolute log ratio."""
    return np.mean(np.abs(np.log(1 + predictions) - np.log(1 + y_true)))

  def report(self, name=None):
    if name is not None:
      print_string = '{} results'.format(name)
      print(print_string)
      print('~' * len(print_string))
    print('RMSE: {:2.3f}\nMAE: {:2.3f}\nMALR: {:2.3f}'.format(
        self.rmse, self.mae, self.malr))
