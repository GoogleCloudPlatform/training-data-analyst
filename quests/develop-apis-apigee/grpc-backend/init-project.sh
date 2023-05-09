# retrieve FIRESTORE_LOCATION
MYDIR="$(dirname "$0")"
source "${MYDIR}/config.sh"

if [[ -z "${FIRESTORE_LOCATION}" ]]; then
  echo "*** FIRESTORE_LOCATION not set ***"
  exit 1
fi

# enable Cloud Run APIs
echo "*** enable Cloud Run APIs ***"
gcloud services enable run.googleapis.com

# create Firestore in Native mode database
echo "*** create Firestore database ***"
gcloud firestore databases create --location=${FIRESTORE_LOCATION} --type=firestore-native
