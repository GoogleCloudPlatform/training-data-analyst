# retrieve GOOGLE_PROJECT_ID and CLOUDRUN_REGION
MYDIR="$(dirname "$0")"
source "${MYDIR}/config.sh"

if [[ -z "${GOOGLE_PROJECT_ID}" ]]; then
  echo "GOOGLE_PROJECT_ID not set"
  exit 1
fi

if [[ -z "${CLOUDRUN_REGION}" ]]; then
  echo "CLOUDRUN_REGION not set"
  exit 1
fi

# create service account for Apigee to access Cloud Run service
gcloud iam service-accounts create apigee-internal-access \
  --display-name="Service account for internal access by Apigee proxies" \
  --project=${GOOGLE_PROJECT_ID}

# add permission to invoke service
gcloud run services add-iam-policy-binding simplebank \
  --member="serviceAccount:apigee-internal-access@${GOOGLE_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.invoker" --region=${CLOUDRUN_REGION} \
  --project=${GOOGLE_PROJECT_ID}
