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
export SVCACCT_ROLE2="roles/run.builder"

# create service account for Cloud Run service
echo "*** creating Cloud Run service account: ${SVCACCT_EMAIL} ***"
gcloud iam service-accounts create ${SVCACCT_NAME} \
  --display-name="Simplebank(REST) service account" \
  --project=${GOOGLE_PROJECT_ID}

# add permission to access Firestore
echo "*** adding role ${SVCACCT_ROLE} for Firestore access ***"

retries=5
delay=15
count=0

until gcloud projects add-iam-policy-binding ${GOOGLE_PROJECT_ID} \
  --member="serviceAccount:${SVCACCT_EMAIL}" \
  --role=${SVCACCT_ROLE}
do
  count=$((count+1))
  if [[ ${count} -ge ${retries} ]]; then
    echo "Policy binding failed after ${retries} attempts."
    exit 1
  fi
  echo "Policy binding failed, likely due to IAM propagation delay. Retrying in ${delay}s... (${count}/${retries})"
  sleep ${delay}
done

# add permission to access Cloud Run, second binding should work the first time
echo "*** adding role ${SVCACCT_ROLE2} for Cloud Run access ***"
gcloud projects add-iam-policy-binding ${GOOGLE_PROJECT_ID} \
  --member="serviceAccount:${SVCACCT_EMAIL}" \
  --role=${SVCACCT_ROLE2}
