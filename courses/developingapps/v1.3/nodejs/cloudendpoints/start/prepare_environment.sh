# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

echo "Creating App Engine app"
gcloud app create --region "us-central"

echo "Making bucket: gs://$DEVSHELL_PROJECT_ID-media"
gsutil mb gs://$DEVSHELL_PROJECT_ID-media

echo "Exporting GCLOUD_PROJECT and GCLOUD_BUCKET"
export GCLOUD_PROJECT=$DEVSHELL_PROJECT_ID
export GCLOUD_BUCKET=$DEVSHELL_PROJECT_ID-media
export PROJECT_NUMBER=$(gcloud projects describe "$GCLOUD_PROJECT" \
--format "value(projectNumber)")

gcloud services disable cloudfunctions.googleapis.com
gcloud services enable cloudfunctions.googleapis.com

SERVICE_ACCOUNT=$(gcloud storage service-agent --project=$DEVSHELL_PROJECT_ID)
gcloud projects add-iam-policy-binding $DEVSHELL_PROJECT_ID \
  --member serviceAccount:$SERVICE_ACCOUNT \
  --role roles/pubsub.publisher

nvm install node

echo "Installing dependencies"
npm install
npm update

echo "Installing Open API generator"
npm install -g api2swagger

echo "Creating Datastore entities"
npm install @google-cloud/datastore

node setup/add_entities.js

echo "Creating Cloud Pub/Sub topic"
gcloud pubsub topics create feedback

echo "Creating Cloud Spanner Instance, Database, and Table"
gcloud spanner instances create quiz-instance --config=regional-us-central1 --description="Quiz instance" --nodes=1
gcloud spanner databases create quiz-database --instance quiz-instance --ddl "CREATE TABLE Feedback ( feedbackId STRING(100) NOT NULL, email STRING(100), quiz STRING(20), feedback STRING(MAX), rating INT64, score FLOAT64, timestamp INT64 ) PRIMARY KEY (feedbackId);"

echo "Enabling Cloud Functions API"
gcloud services enable cloudfunctions.googleapis.com
echo "Creating Cloud Function"
gcloud functions deploy process-feedback --gen2 --runtime nodejs14 --region us-central1 --trigger-topic feedback --source ./function --stage-bucket $GCLOUD_BUCKET --entry-point subscribe --allow-unauthenticated

echo "Project ID: $DEVSHELL_PROJECT_ID"
