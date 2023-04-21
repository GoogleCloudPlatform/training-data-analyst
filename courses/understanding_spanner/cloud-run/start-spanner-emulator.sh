# Install the Google Cloud Spanner Emulator
sudo apt-get install google-cloud-sdk-spanner-emulator

# Start the Emulator
gcloud emulators spanner start

# Open another terminal tab and add the following gcloud Configuration
gcloud config configurations create emulator
gcloud config set auth/disable_credentials true
#########################################################
# Make sure to set the project ID in the statement below
gcloud config set project roi-spanner
#########################################################
gcloud config set api_endpoint_overrides/spanner http://localhost:9020/

# Create an Instance in the Emulator
gcloud spanner instances create emulator-instance \
   --config=emulator-config --description="EmulatorInstance" --nodes=1

# See if it worked
gcloud spanner instances list

# Create the Spanner database. Make sure this is run from the 
# folder where the Schema File is (./pets-db-schema.sql)
gcloud spanner databases create pets-db --instance=emulator-instance --database-dialect=GOOGLE_STANDARD_SQL --ddl-file=./pets-db-schema.sql

# Need to set the following Environment Variable for the 
# Client Library to use the Emulator
export SPANNER_EMULATOR_HOST=localhost:9010


# To switch between emulator and default gcloud configurations
# gcloud config configurations activate [emulator | default]