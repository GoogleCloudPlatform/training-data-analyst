GOOGLE_PROJECT_ID=REPLACETHIS
GOOGLE_PROJECT_ID=simplebank-backend
REGION=us-central1

# enable Cloud Run APIs
gcloud services enable run.googleapis.com

# create service account for Cloud Run service
gcloud iam service-accounts create simplebank-grpc \
  --display-name="Simplebank(gRPC) service account" \
  --project=${GOOGLE_PROJECT_ID}

# add permission to access firestore (datastore in firestore mode)
gcloud projects add-iam-policy-binding ${GOOGLE_PROJECT_ID} \
  --member="serviceAccount:simplebank-grpc@${GOOGLE_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/datastore.user"
