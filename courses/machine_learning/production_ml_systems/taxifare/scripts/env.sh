# Replace with appropriate values.
IMAGE_NAME=taxifare_training_container
BUCKET=ml-on-gcp-test
REGION=us-west1

BATCH_SIZE=5
NUM_EXAMPLES_TO_TRAIN_ON=100
NUM_EVALS=1
NBUCKETS=10
NNSIZE="32 8"

# Generated.
GCS_PROJECT_PATH=gs://$BUCKET/taxifare
DATA_PATH=$GCS_PROJECT_PATH/data
OUTPUT_DIR=$GCS_PROJECT_PATH/model
TRAIN_DATA_PATH=$DATA_PATH/taxi-train*
EVAL_DATA_PATH=$DATA_PATH/taxi-valid*

JOBID=${IMAGE_NAME}_$(date +%Y%m%d_%H%M%S)
SCRIPTS_DIR=$(cd $(dirname $BASH_SOURCE) && pwd)
PROJECT_DIR=$(dirname $SCRIPTS_DIR)
PROJECT_ID=$(gcloud config list project --format "value(core.project)")
IMAGE_URI=gcr.io/$PROJECT_ID/$IMAGE_NAME
DOCKERFILE=$PROJECT_DIR/Dockerfile
