# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Model features metadata utils."""

FEATURES = [
    "trip_month",
    "trip_day",
    "trip_day_of_week",
    "trip_hour",
    "trip_seconds",
    "trip_miles",
    "payment_type",
    "pickup_grid",
    "dropoff_grid",
    "euclidean",
    "loc_cross",
]

TARGET = "tip_bin"

TARGET_LABELS = ["tip<20%", "tip>=20%"]