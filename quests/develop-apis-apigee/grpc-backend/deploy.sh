GOOGLE_PROJECT_ID=REPLACETHIS
GOOGLE_PROJECT_ID=simplebank-backend
REGION=us-central1

# build simplebank image from code
gcloud builds submit --tag gcr.io/${GOOGLE_PROJECT_ID}/simplebank-grpc \
  --project=${GOOGLE_PROJECT_ID}

# deploy service
# NOTE: in a production environment, you would not use max-instances=1
gcloud run deploy simplebank-grpc \
  --image=gcr.io/${GOOGLE_PROJECT_ID}/simplebank-grpc \
  --platform=managed \
  --max-instances=1 \
  --region=${REGION} \
  --no-allow-unauthenticated \
  --service-account=simplebank@${GOOGLE_PROJECT_ID}.iam.gserviceaccount.com \
  --project=${GOOGLE_PROJECT_ID}
