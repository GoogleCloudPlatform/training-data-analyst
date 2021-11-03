# retrieve GOOGLE_PROJECT_ID and REGION
MYDIR="$(dirname "$0")"
source "${MYDIR}/config.sh"

if [[ -z "${GOOGLE_PROJECT_ID}" ]]; then
  echo "GOOGLE_PROJECT_ID not set"
  exit 1
fi

if [[ -z "${REGION}" ]]; then
  echo "REGION not set"
  exit 1
fi

# build simplebank-rest image from code
gcloud builds submit --tag gcr.io/${GOOGLE_PROJECT_ID}/simplebank-rest \
  --project=${GOOGLE_PROJECT_ID}

# deploy service
# NOTE: in a production environment, you would not use max-instances=1
gcloud run deploy simplebank-rest \
  --image=gcr.io/${GOOGLE_PROJECT_ID}/simplebank-rest \
  --platform=managed \
  --max-instances=1 \
  --region=${REGION} \
  --no-allow-unauthenticated \
  --service-account=simplebank@${GOOGLE_PROJECT_ID}.iam.gserviceaccount.com \
  --project=${GOOGLE_PROJECT_ID}
