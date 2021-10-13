#GOOGLE_PROJECT_ID=# YOUR GCP PROJECT ID GOES HERE
GOOGLE_PROJECT_ID=simplebank-backend

gcloud builds submit --tag gcr.io/$GOOGLE_PROJECT_ID/simplebankapi \
  --project=$GOOGLE_PROJECT_ID

gcloud run deploy simplebank \
  --image=gcr.io/$GOOGLE_PROJECT_ID/simplebankapi \
  --platform=managed \
  --region=us-central1 \
  --no-allow-unauthenticated \
  --project=$GOOGLE_PROJECT_ID
