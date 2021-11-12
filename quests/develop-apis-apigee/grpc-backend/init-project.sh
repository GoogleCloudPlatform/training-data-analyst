# retrieve APP_REGION
MYDIR="$(dirname "$0")"
source "${MYDIR}/config.sh"

if [[ -z "${APP_REGION}" ]]; then
  echo "*** APP_REGION not set ***"
  exit 1
fi

# enable Cloud Run APIs
echo "*** enable Cloud Run APIs ***"
gcloud services enable run.googleapis.com

# create App Engine app (prerequisite for Firestore in Native mode)
echo "*** create App Engine app (required for Firestore) ***"
gcloud app create --region=${APP_REGION}

# create Firestore in Native mode database
echo "*** create Firestore database ***"
gcloud firestore databases create --region=${APP_REGION}
