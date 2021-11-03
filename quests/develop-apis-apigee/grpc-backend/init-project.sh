# retrieve REGION
MYDIR="$(dirname "$0")"
source "${MYDIR}/config.sh"

if [[ -z "${REGION}" ]]; then
  echo "REGION not set"
  exit 1
fi

# enable Cloud Run APIs
gcloud services enable run.googleapis.com

# create app engine app (prerequisite for Firestore in Native mode)
gcloud app create --region=${REGION}

# create Firestore in Native mode database
gcloud firestore databases create --region=${REGION}
