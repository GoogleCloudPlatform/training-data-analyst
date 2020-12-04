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

echo "Creating Compute Engine instance"
gcloud compute firewall-rules create default-allow-http --allow tcp:80 --source-ranges 0.0.0.0/0 --target-tags http-server
gcloud compute instances create endpoint-host --zone us-central1-a --tags http-server --scopes=cloud-platform --metadata endpoints-service-name="quiz-api.endpoints.$GCLOUD_PROJECT.cloud.goog",endpoints-service-config-id="`date +%Y-%m-%d`r0" --metadata-from-file=startup-script=./setup/endpointhost_startup_script.sh

echo "Creating App Engine app"
gcloud app create --region "us-central"

echo "Making bucket: gs://$GCLOUD_BUCKET"
gsutil mb gs://$GCLOUD_BUCKET

echo "Installing dependencies"
npm install -g npm@6.11.3
npm update

echo "Installing Open API generator"
npm install -g api2swagger

echo "Creating Datastore entities"
node setup/add_entities.js

echo "Creating Cloud Pub/Sub topic"
gcloud pubsub topics create feedback

echo "Creating Cloud Spanner Instance, Database, and Table"
gcloud spanner instances create quiz-instance --config=regional-us-central1 --description="Quiz instance" --nodes=1
gcloud spanner databases create quiz-database --instance quiz-instance --ddl "CREATE TABLE Feedback ( feedbackId STRING(100) NOT NULL, email STRING(100), quiz STRING(20), feedback STRING(MAX), rating INT64, score FLOAT64, timestamp INT64 ) PRIMARY KEY (feedbackId);"

echo "Enabling Cloud Functions API"
gcloud services enable cloudfunctions.googleapis.com
echo "Creating Cloud Function"
gcloud functions deploy process-feedback --runtime nodejs12 --trigger-topic feedback --source ./function --stage-bucket $GCLOUD_BUCKET --entry-point subscribe

echo "Creating Cloud Endpoint"
sed -i "s/GCLOUD_PROJECT/$GCLOUD_PROJECT/g" ./endpoint/quiz-api.json
gcloud endpoints services deploy ./endpoint/quiz-api.json
export SERVICEID=$(gcloud endpoints services describe quiz-api.endpoints.$GCLOUD_PROJECT.cloud.goog --format='value('serviceConfig.id')')

gcloud compute instances add-metadata endpoint-host --zone us-central1-a \
  --metadata endpoints-service-name="quiz-api.endpoints.$GCLOUD_PROJECT.cloud.goog",endpoints-service-config-id="$SERVICEID"

echo "Copying source to Compute Engine"
gcloud compute scp --force-key-file-overwrite --quiet --recurse ./endpoint/quiz-api endpoint-host:~/ --zone us-central1-a


echo "Installing and running Cloud Endpoint backend"
gcloud compute ssh endpoint-host --zone us-central1-a --command "export PORT=8081 && export GCLOUD_PROJECT=$(gcloud info --format='value(config.project)') && export GCLOUD_BUCKET=$GCLOUD_PROJECT-media && cd ~/quiz-api && sudo npm install -g npm@6.11.3 && sudo npm update && npm start"
#gcloud compute ssh endpoint-host --zone us-central1-a --command "export PORT=8081 && export GCLOUD_PROJECT=$DEVSHELL_PROJECT_ID && export GCLOUD_BUCKET=$DEVSHELL_PROJECT_ID-media && cd ~/quiz-api && sudo npm install -g npm@6.11.3 && sudo npm update && npm start"

echo "Project ID: $DEVSHELL_PROJECT_ID"
