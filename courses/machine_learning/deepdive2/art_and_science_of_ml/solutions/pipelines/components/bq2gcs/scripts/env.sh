SCRIPTS_DIR=$(cd $(dirname $BASH_SOURCE) && pwd)
COMPONENT_DIR=$(dirname $SCRIPTS_DIR)
COMPONENT_NAME=$(basename $COMPONENT_DIR)
PROJECT_ID=$(gcloud config list project --format "value(core.project)")
IMAGE_NAME=taxifare-$COMPONENT_NAME
IMAGE_URI=gcr.io/$PROJECT_ID/$IMAGE_NAME
DOCKERFILE=$COMPONENT_DIR/Dockerfile
