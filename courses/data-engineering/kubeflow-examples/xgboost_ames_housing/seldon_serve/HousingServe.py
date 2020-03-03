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

import joblib
import numpy as np

class HousingServe(object):
  def __init__(self, model_file='housing.dat'):
    """Load the housing model using joblib."""
    self.model = joblib.load(model_file)

  def predict(self, X, feature_names):
    """Predict using the model for given ndarray."""
    prediction = self.model.predict(data=X)
    print(feature_names)

    # added this temporarily to keep seldon happy
    # TODO: http://bit.ly/2Pvexmb
    return [[prediction.item(0), prediction.item(0)]]


if __name__ == '__main__':
  serve = HousingServe()
  print(serve.predict(np.ndarray([1, 37]), None))
