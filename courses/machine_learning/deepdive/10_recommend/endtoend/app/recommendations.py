# Copyright 2017 Google Inc. All Rights Reserved.
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

"""Recommendation generation module."""

import logging
import numpy as np
import os
import pandas as pd

import google.auth
import google.cloud.storage as storage

logging.basicConfig(level=logging.INFO)

LOCAL_MODEL_PATH = '/tmp'

ROW_MODEL_FILE = 'model/row.npy'
COL_MODEL_FILE = 'model/col.npy'
USER_MODEL_FILE = 'model/user.npy'
ITEM_MODEL_FILE = 'model/item.npy'
USER_ITEM_DATA_FILE = 'data/recommendation_events.csv'


class Recommendations(object):
  """Provide recommendations from a pre-trained collaborative filtering model.

  Args:
    local_model_path: (string) local path to model files
  """

  def __init__(self, local_model_path=LOCAL_MODEL_PATH):
    _, project_id = google.auth.default()
    self._bucket = 'recserve_' + project_id
    self._load_model(local_model_path)

  def _load_model(self, local_model_path):
    """Load recommendation model files from GCS.

    Args:
      local_model_path: (string) local path to model files
    """
    # download files from GCS to local storage
    os.makedirs(os.path.join(local_model_path, 'model'), exist_ok=True)
    os.makedirs(os.path.join(local_model_path, 'data'), exist_ok=True)
    client = storage.Client()
    bucket = client.get_bucket(self._bucket)

    logging.info('Downloading blobs.')

    model_files = [ROW_MODEL_FILE, COL_MODEL_FILE, USER_MODEL_FILE,
                   ITEM_MODEL_FILE, USER_ITEM_DATA_FILE]
    for model_file in model_files:
      blob = bucket.blob(model_file)
      with open(os.path.join(local_model_path, model_file), 'wb') as file_obj:
        blob.download_to_file(file_obj)

    logging.info('Finished downloading blobs.')

    # load npy arrays for user/item factors and user/item maps
    self.user_factor = np.load(os.path.join(local_model_path, ROW_MODEL_FILE))
    self.item_factor = np.load(os.path.join(local_model_path, COL_MODEL_FILE))
    self.user_map = np.load(os.path.join(local_model_path, USER_MODEL_FILE))
    self.item_map = np.load(os.path.join(local_model_path, ITEM_MODEL_FILE))

    logging.info('Finished loading arrays.')

    # load user_item history into pandas dataframe
    views_df = pd.read_csv(os.path.join(local_model_path,
                                        USER_ITEM_DATA_FILE), sep=',', header=0)
    self.user_items = views_df.groupby('clientId')

    logging.info('Finished loading model.')

  def get_recommendations(self, user_id, num_recs):
    """Given a user id, return list of num_recs recommended item ids.

    Args:
      user_id: (string) The user id
      num_recs: (int) The number of recommended items to return

    Returns:
      [item_id_0, item_id_1, ... item_id_k-1]: The list of k recommended items,
        if user id is found.
      None: The user id was not found.
    """
    article_recommendations = None

    # map user id into ratings matrix user index
    user_idx = np.searchsorted(self.user_map, user_id)

    if user_idx:
      # get already viewed items from views dataframe
      already_rated = self.user_items.get_group(user_id).contentId
      already_rated_idx = [np.searchsorted(self.item_map, i)
                           for i in already_rated]

      # generate list of recommended article indexes from model
      recommendations = generate_recommendations(user_idx, already_rated_idx,
                                                 self.user_factor,
                                                 self.item_factor,
                                                 num_recs)

      # map article indexes back to article ids
      article_recommendations = [self.item_map[i] for i in recommendations]

    return article_recommendations


def generate_recommendations(user_idx, user_rated, row_factor, col_factor, k):
  """Generate recommendations for a user.

  Args:
    user_idx: the row index of the user in the ratings matrix,

    user_rated: the list of item indexes (column indexes in the ratings matrix)
      previously rated by that user (which will be excluded from the
      recommendations),

    row_factor: the row factors of the recommendation model

    col_factor: the column factors of the recommendation model

    k: number of recommendations requested

  Returns:
    list of k item indexes with the predicted highest rating,
    excluding those that the user has already rated
  """

  # bounds checking for args
  assert (row_factor.shape[0] - len(user_rated)) >= k

  # retrieve user factor
  user_f = row_factor[user_idx]

  # dot product of item factors with user factor gives predicted ratings
  pred_ratings = col_factor.dot(user_f)

  # find candidate recommended item indexes sorted by predicted rating
  k_r = k + len(user_rated)
  candidate_items = np.argsort(pred_ratings)[-k_r:]

  # remove previously rated items and take top k
  recommended_items = [i for i in candidate_items if i not in user_rated]
  recommended_items = recommended_items[-k:]

  # flip to sort highest rated first
  recommended_items.reverse()

  return recommended_items

