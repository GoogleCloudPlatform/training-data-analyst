export PROJECT_ID=$(gcloud config list project --format "value(core.project)")
export IMAGE_REPO_NAME=babyweight_training_container
export IMAGE_URI=gcr.io/${PROJECT_ID}/${IMAGE_REPO_NAME}

echo "Building  $IMAGE_URI"
docker build -f Dockerfile -t ${IMAGE_URI} ./
echo "Pushing $IMAGE_URI"
docker push ${IMAGE_URI}