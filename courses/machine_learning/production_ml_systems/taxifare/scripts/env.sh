# Replace with appropriate values.
IMAGE_REPO_NAME=serverlessml_training_container
BUCKET=ml-on-gcp-test
REGION=us-west1

# Generated.
JOBID=${IMAGE_REPO_NAME}_$(date +%Y%m%d_%H%M%S)
SCRIPTS_DIR=$(cd $(dirname $BASH_SOURCE) && pwd)
PROJECT_DIR=$(dirname $SCRIPTS_DIR)
PROJECT_ID=$(gcloud config list project --format "value(core.project)")
IMAGE_URI=gcr.io/$PROJECT_ID/$IMAGE_REPO_NAME
DOCKERFILE=$PROJECT_DIR/Dockerfile
