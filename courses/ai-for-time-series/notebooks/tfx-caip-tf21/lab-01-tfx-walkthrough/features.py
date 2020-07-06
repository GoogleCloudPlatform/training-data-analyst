# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Covertype model  taxi model features."""
import tensorflow as tf
import tensorflow_model_analysis as tfma
import tensorflow_transform as tft
from tensorflow_transform.tf_metadata import schema_utils

NUMERIC_FEATURE_KEYS = [f't{x:+}' for x in range(-29,1)] + [f'h{x:+}' for x in range(-29,1)]

CATEGORICAL_FEATURE_KEYS = []

LABEL_KEYS = [f't{x:+}' for x in range(1,8)]

def transformed_name(key):
  return key + '_xf'

