# retrieve GOOGLE_PROJECT_ID and CLOUDRUN_REGION
MYDIR="$(dirname "$0")"
source "${MYDIR}/config.sh"

if [[ -z "${GOOGLE_PROJECT_ID}" ]]; then
  echo "*** GOOGLE_PROJECT_ID not set ***"
  exit 1
fi

if [[ -z "${CLOUDRUN_REGION}" ]]; then
  echo "*** CLOUDRUN_REGION not set ***"
  exit 1
fi

export SERVICE_NAME="simplebank-rest"
export SVCACCT_NAME="simplebank-rest"
export SVCACCT_EMAIL="${SVCACCT_NAME}@${GOOGLE_PROJECT_ID}.iam.gserviceaccount.com"

# deploy service
# NOTE: in a production environment, you would not use max-instances=1
echo "*** deploy ${SERVICE_NAME} service to ${CLOUDRUN_REGION} with service account ${SVCACCT_EMAIL} (with retries) ***"

retries=5
delay=15
count=0

until gcloud run deploy ${SERVICE_NAME} \
  --platform=managed \
  --max-instances=1 \
  --region=${CLOUDRUN_REGION} \
  --no-allow-unauthenticated \
  --service-account=${SVCACCT_EMAIL} \
  --build-service-account=projects/${GOOGLE_PROJECT_ID}/serviceAccounts/${SVCACCT_EMAIL} \
  --project=${GOOGLE_PROJECT_ID} \
  --quiet \
  --source .
do
  count=$((count+1))
  if [[ ${count} -ge ${retries} ]]; then
    echo "Deployment failed after ${retries} attempts."
    exit 1
  fi
  echo "Deployment failed, likely due to IAM propagation delay. Retrying in ${delay}s... (${count}/${retries})"
  sleep ${delay}
done

