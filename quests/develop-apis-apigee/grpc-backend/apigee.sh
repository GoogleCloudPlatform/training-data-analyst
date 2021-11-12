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

SERVICE_NAME="simplebank-grpc"
APIGEE_SVCACCT_NAME="apigee-internal-access"
APIGEE_SVCACCT_EMAIL="${APIGEE_SVCACCT_NAME}@${GOOGLE_PROJECT_ID}.iam.gserviceaccount.com"
APIGEE_SVCACCT_ROLE="roles/run.invoker"

# create service account for Apigee to access Cloud Run service
echo "*** creating Apigee service account: ${APIGEE_SVCACCT_EMAIL} ***"
gcloud iam service-accounts create ${APIGEE_SVCACCT_NAME} \
  --display-name="Service account for internal access by Apigee proxies" \
  --project=${GOOGLE_PROJECT_ID}

# add permission to invoke gRPC service
echo "*** adding role ${APIGEE_SVCACCT_ROLE} for service ${SERVICE_NAME} ***"
gcloud run services add-iam-policy-binding ${SERVICE_NAME} \
  --member="serviceAccount:${APIGEE_SVCACCT_EMAIL}" \
  --role=${APIGEE_SVCACCT_ROLE} --region=${CLOUDRUN_REGION} \
  --project=${GOOGLE_PROJECT_ID}
