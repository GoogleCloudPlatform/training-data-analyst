# retrieve GOOGLE_PROJECT_ID
MYDIR="$(dirname "$0")"
source "${MYDIR}/config.sh"

if [[ -z "${GOOGLE_PROJECT_ID}" ]]; then
  echo "*** GOOGLE_PROJECT_ID not set ***"
  exit 1
fi

export SVCACCT_NAME="simplebank-rest"
export SVCACCT_EMAIL="${SVCACCT_NAME}@${GOOGLE_PROJECT_ID}.iam.gserviceaccount.com"
export SVCACCT_ROLE="roles/datastore.user"
export SVCACCT_ROLE2="cloudbuild.builds.builder"

# create service account for Cloud Run service
echo "*** creating Cloud Run service account: ${SVCACCT_EMAIL} ***"
gcloud iam service-accounts create ${SVCACCT_NAME} \
  --display-name="Simplebank(REST) service account" \
  --project=${GOOGLE_PROJECT_ID}

# add permission to access Firestore
echo "*** adding role ${SVCACCT_ROLE} for Firestore access ***"
gcloud projects add-iam-policy-binding ${GOOGLE_PROJECT_ID} \
  --member="serviceAccount:${SVCACCT_EMAIL}" \
  --role=${SVCACCT_ROLE}

# add permission to access Cloud Build
echo "*** adding role ${SVCACCT_ROLE} for Firestore access ***"
gcloud projects add-iam-policy-binding ${GOOGLE_PROJECT_ID} \
  --member="serviceAccount:${SVCACCT_EMAIL}" \
  --role=${SVCACCT_ROLE2}
