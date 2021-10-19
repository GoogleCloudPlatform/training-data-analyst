GOOGLE_PROJECT_ID=# YOUR GCP PROJECT ID GOES HERE
REGION=us-central1

# create service account for Cloud Run service
gcloud iam service-accounts create simplebank \
  --display-name="Simplebank service account" \
  --project=${GOOGLE_PROJECT_ID}

# add permission to access firestore (datastore in firestore mode)
gcloud projects add-iam-policy-binding ${GOOGLE_PROJECT_ID} \
  --member="serviceAccount:simplebank@${GOOGLE_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/datastore.user"

# create service account for Apigee to access Cloud Run service
gcloud iam service-accounts create apigee-internal-access \
  --display-name="Service account for internal access by Apigee proxies" \
  --project=${GOOGLE_PROJECT_ID}

# add permission to invoke service
gcloud run services add-iam-policy-binding simplebank \
  --member="serviceAccount:apigee-internal-access@${GOOGLE_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.invoker" --region=${REGION} \
  --project=${GOOGLE_PROJECT_ID}