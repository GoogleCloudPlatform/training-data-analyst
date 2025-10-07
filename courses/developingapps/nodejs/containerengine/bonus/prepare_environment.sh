# Copyright 2017 Google Inc.
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
echo "Exporting GCLOUD_PROJECT and GCLOUD_BUCKET"
export GCLOUD_PROJECT=$DEVSHELL_PROJECT_ID
export GCLOUD_BUCKET=$DEVSHELL_PROJECT_ID-media

echo "Creating App Engine app"
gcloud app create --region "us-central"

echo "Making bucket: gs://$GCLOUD_BUCKET"
gcloud storage buckets create gs://$GCLOUD_BUCKET

echo "Installing dependencies"
npm install

echo "Creating Datastore entities"
node setup/add_entities.js

echo "Creating Cloud Pub/Sub topics"
gcloud pubsub topics create feedback
gcloud pubsub subscriptions create worker-subscription --topic=feedback
gcloud pubsub topics create answers

echo "Creating Cloud Spanner Instance, Database, and Tables"
gcloud spanner instances create quiz-instance --config=regional-us-central1 --description="Quiz instance" --nodes=1
gcloud spanner databases create quiz-database --instance quiz-instance --ddl "CREATE TABLE Feedback ( feedbackId STRING(100) NOT NULL, email STRING(100), quiz STRING(20), feedback STRING(MAX), rating INT64, score FLOAT64, timestamp INT64 ) PRIMARY KEY (feedbackId); CREATE TABLE Answers (answerId STRING(100) NOT NULL, id INT64, email STRING(60), quiz STRING(20), answer INT64, correct INT64, timestamp INT64) PRIMARY KEY (answerId DESC);"

echo "Creating Container Engine cluster"
gcloud container clusters create quiz-cluster --zone us-central1-a --scopes cloud-platform
gcloud container clusters get-credentials quiz-cluster --zone us-central1-a

echo "Building Containers"
gcloud container builds submit -t gcr.io/$DEVSHELL_PROJECT_ID/quiz-frontend ./frontend/
gcloud container builds submit -t gcr.io/$DEVSHELL_PROJECT_ID/quiz-backend ./backend/
gcloud container builds submit -t gcr.io/$DEVSHELL_PROJECT_ID/quiz-answer-backend ./answer_backend/

echo "Deploying to Container Engine"
sed -i -e "s/\[GCLOUD_PROJECT\]/$DEVSHELL_PROJECT_ID/g" ./frontend-deployment.yaml
sed -i -e "s/\[GCLOUD_PROJECT\]/$DEVSHELL_PROJECT_ID/g" ./backend-deployment.yaml
sed -i -e "s/\[GCLOUD_PROJECT\]/$DEVSHELL_PROJECT_ID/g" ./answer-backend-deployment.yaml
kubectl create -f ./frontend-deployment.yaml
kubectl create -f ./backend-deployment.yaml
kubectl create -f ./answer-backend-deployment.yaml
kubectl create -f ./frontend-service.yaml


echo "Project ID: $DEVSHELL_PROJECT_ID"
