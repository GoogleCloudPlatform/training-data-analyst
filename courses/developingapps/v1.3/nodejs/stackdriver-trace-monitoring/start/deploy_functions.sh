# Copyright 2024 Google Inc.
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

echo "Exporting GCLOUD_BUCKET"
export GCLOUD_BUCKET=$DEVSHELL_PROJECT_ID-media

echo "Creating Cloud Functions"
gcloud functions deploy process-feedback --runtime nodejs20 --trigger-topic feedback --source ./functions/feedback --stage-bucket $GCLOUD_BUCKET --entry-point subscribe
gcloud functions deploy process-answer --runtime nodejs20 --trigger-topic answers --source ./functions/answer --stage-bucket $GCLOUD_BUCKET --entry-point subscribe
