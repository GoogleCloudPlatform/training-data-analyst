# Copyright 2018 Google Inc. All Rights Reserved.
#
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

PROJECT = None
KEYDIR  = 'trainer'

def create_queries():
  query_all = """
  WITH with_ultrasound AS (
    SELECT
      weight_pounds AS label,
      CAST(is_male AS STRING) AS is_male,
      mother_age,
      CAST(plurality AS STRING) AS plurality,
      gestation_weeks,
      ABS(FARM_FINGERPRINT(CONCAT(CAST(YEAR AS STRING), CAST(month AS STRING)))) AS hashmonth
    FROM
      publicdata.samples.natality
    WHERE
      year > 2000
      AND gestation_weeks > 0
      AND mother_age > 0
      AND plurality > 0
      AND weight_pounds > 0
  ),

  without_ultrasound AS (
    SELECT
      weight_pounds AS label,
      'Unknown' AS is_male,
      mother_age,
      IF(plurality > 1, 'Multiple', 'Single') AS plurality,
      gestation_weeks,
      ABS(FARM_FINGERPRINT(CONCAT(CAST(YEAR AS STRING), CAST(month AS STRING)))) AS hashmonth
    FROM
      publicdata.samples.natality
    WHERE
      year > 2000
      AND gestation_weeks > 0
      AND mother_age > 0
      AND plurality > 0
      AND weight_pounds > 0
  ),

  preprocessed AS (
    SELECT * from with_ultrasound
    UNION ALL
    SELECT * from without_ultrasound
  )

  SELECT
      label,
      is_male,
      mother_age,
      plurality,
      gestation_weeks
  FROM
      preprocessed
  """

  train_query = "{} WHERE MOD(hashmonth, 4) < 3".format(query_all)
  eval_query  = "{} WHERE MOD(hashmonth, 4) = 3".format(query_all)
  return train_query, eval_query

def query_to_dataframe(query):
  import pandas as pd
  import pkgutil, json
  privatekey = pkgutil.get_data(KEYDIR, 'privatekey.json')
  print(privatekey[:200])
  return pd.read_gbq(query, 
                     project_id=PROJECT, 
                     dialect='standard',
                     private_key=privatekey)

def create_dataframes(frac):  
  # small dataset for testing
  if frac > 0 and frac < 1:
    sample = " AND RAND() < {}".format(frac)
  else:
    sample = ""

  train_query, eval_query = create_queries()
  train_query = "{} {}".format(train_query, sample)
  eval_query =  "{} {}".format(eval_query, sample)

  train_df = query_to_dataframe(train_query)
  eval_df = query_to_dataframe(eval_query)
  return train_df, eval_df

def input_fn(indf):
  import copy
  import pandas as pd
  df = copy.deepcopy(indf)

  # one-hot encode the categorical columns
  df["plurality"] = df["plurality"].astype(pd.api.types.CategoricalDtype(
                  categories=["Single","Multiple","1","2","3","4","5"]))
  df["is_male"] = df["is_male"].astype(pd.api.types.CategoricalDtype(
                  categories=["Unknown","false","true"]))
  # features, label
  label = df['label']
  del df['label']
  features = pd.get_dummies(df)
  return features, label

def train_and_evaluate(frac, max_depth=5, n_estimators=100):
  import numpy as np

  # get data
  train_df, eval_df = create_dataframes(frac)
  train_x, train_y = input_fn(train_df)
  # train
  from sklearn.ensemble import RandomForestRegressor
  estimator = RandomForestRegressor(max_depth=max_depth, n_estimators=n_estimators, random_state=0)
  estimator.fit(train_x, train_y)
  # evaluate
  eval_x, eval_y = input_fn(eval_df)
  eval_pred = estimator.predict(eval_x)
  rmse = np.sqrt(np.mean((eval_pred-eval_y)*(eval_pred-eval_y)))
  print("Eval rmse={}".format(rmse))
  return estimator, rmse

def save_model(estimator, gcspath, name):
  from sklearn.externals import joblib
  import os, subprocess, datetime
  model = 'model.joblib'
  joblib.dump(estimator, model)
  model_path = os.path.join(gcspath, datetime.datetime.now().strftime(
    'export_%Y%m%d_%H%M%S'), model)
  subprocess.check_call(['gsutil', 'cp', model, model_path])
  return model_path
