# retrieve APP_REGION
MYDIR="$(dirname "$0")"
source "${MYDIR}/config.sh"

if [[ -z "${APP_REGION}" ]]; then
  echo "APP_REGION not set"
  exit 1
fi

# enable Cloud Run APIs
gcloud services enable run.googleapis.com

# create app engine app (prerequisite for Firestore in Native mode)
gcloud app create --region=${APP_REGION}

# create Firestore in Native mode database
gcloud firestore databases create --region=${APP_REGION}
