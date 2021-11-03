# retrieve GOOGLE_PROJECT_ID
MYDIR="$(dirname "$0")"
source "${MYDIR}/config.sh"

if [[ -z "${GOOGLE_PROJECT_ID}" ]]; then
  echo "GOOGLE_PROJECT_ID not set"
  exit 1
fi

# create service account for Cloud Run service
gcloud iam service-accounts create simplebank-rest \
  --display-name="Simplebank(REST) service account" \
  --project=${GOOGLE_PROJECT_ID}

# add permission to access firestore (datastore in firestore mode)
gcloud projects add-iam-policy-binding ${GOOGLE_PROJECT_ID} \
  --member="serviceAccount:simplebank-rest@${GOOGLE_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/datastore.user"
