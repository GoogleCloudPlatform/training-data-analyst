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

echo "Enabling Cloud Functions API"
gcloud services enable cloudfunctions.googleapis.com

echo "Creating App Engine app"
gcloud app create --region "us-central"

echo "Exporting GCLOUD_PROJECT and GCLOUD_BUCKET and NODE_ENV"
export GCLOUD_PROJECT=$DEVSHELL_PROJECT_ID
export GCLOUD_BUCKET=$DEVSHELL_PROJECT_ID-media
export NODE_ENV=production

echo "Making bucket: gs://$GCLOUD_BUCKET"
gsutil mb gs://$GCLOUD_BUCKET

echo "Installing dependencies"
npm install
npm update

echo "Creating Datastore entities"
npm install @google-cloud/datastore
node setup/add_entities.js

echo "Creating Cloud Pub/Sub topics"
gcloud pubsub topics create feedback
gcloud pubsub topics create answers

echo "Creating Cloud Spanner Instance, Database, and Tables"
gcloud spanner instances create quiz-instance --config=regional-us-central1 --description="Quiz instance" --nodes=1
gcloud spanner databases create quiz-database --instance quiz-instance --ddl "CREATE TABLE Feedback ( feedbackId STRING(100) NOT NULL, email STRING(100), quiz STRING(20), feedback STRING(MAX), rating INT64, score FLOAT64, timestamp INT64 ) PRIMARY KEY (feedbackId); CREATE TABLE Answers (answerId STRING(100) NOT NULL, id INT64, email STRING(60), quiz STRING(20), answer INT64, correct INT64, timestamp INT64) PRIMARY KEY (answerId DESC);"

echo "Creating Cloud Functions"
gcloud functions deploy process-feedback --runtime nodejs20 --trigger-topic feedback --source ./functions/feedback --stage-bucket $GCLOUD_BUCKET --entry-point subscribe --no-gen2 --region $REGION
gcloud functions deploy process-answer --runtime nodejs20 --trigger-topic answers --source ./functions/answer --stage-bucket $GCLOUD_BUCKET --entry-point subscribe --no-gen2 --region $REGION

echo "Project ID: $GCLOUD_PROJECT"
