GOOGLE_PROJECT_ID=# YOUR GCP PROJECT ID GOES HERE
REGION=us-central1

gcloud builds submit --tag gcr.io/${GOOGLE_PROJECT_ID}/simplebankapi \
  --project=${GOOGLE_PROJECT_ID}

gcloud run deploy simplebank \
  --image=gcr.io/${GOOGLE_PROJECT_ID}/simplebankapi \
  --platform=managed \
  --region=${REGION} \
  --no-allow-unauthenticated \
  --service-account=simplebank@${GOOGLE_PROJECT_ID}.iam.gserviceaccount.com \
  --project=${GOOGLE_PROJECT_ID}
