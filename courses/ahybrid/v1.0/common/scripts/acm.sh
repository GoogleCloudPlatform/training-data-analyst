# Make sure to have role reader
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com \
  --role roles/source.reader

# Enable workload identity to access Cloud Source Repositories
gcloud iam service-accounts add-iam-policy-binding \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:$PROJECT_ID.svc.id.goog[config-management-system/importer]" \
  $PROJECT_NUMBER-compute@developer.gserviceaccount.com

kubectl create namespace config-management-system
kubectl create serviceaccount --namespace config-management-system importer
kubectl annotate serviceaccount -n config-management-system importer \
  iam.gke.io/gcp-service-account=$PROJECT_NUMBER-compute@developer.gserviceaccount.com

# Create a Cloud Source Repository
cd config
export EMAIL=$(curl "http://metadata.google.internal/computeMetadata/v1/instance/attributes/student" -H "Metadata-Flavor: Google")
#export EMAIL=$(curl "http://metadata.google.internal/computeMetadata/v1/instance/attributes/email" -H "Metadata-Flavor: Google")
export USERNAME=$EMAIL
echo $EMAIL
echo $USERNAME
git config --global user.email $EMAIL
git config --global user.name $EMAIL
gcloud source repos create anthos_config
git init
git config credential.helper gcloud.sh
git remote add origin https://source.developers.google.com/p/$PROJECT_ID/r/anthos_config
git add *
git commit -m "Initial commit"
git push --set-upstream origin master
cd ..

# Install Anthos Config Management
cat <<EOF > config-management.yaml
apiVersion: configmanagement.gke.io/v1
kind: ConfigManagement
metadata:
  name: config-management
spec:
  git:
    syncRepo: https://source.developers.google.com/p/$PROJECT_ID/r/anthos_config
    syncBranch: master
    secretType: gcenode
    policyDir: "."
    syncWait: 2
EOF

gcloud services enable anthosconfigmanagement.googleapis.com
sleep 20
gcloud alpha container hub config-management enable
sleep 20
gcloud alpha container hub config-management apply \
  --membership=${C1_NAME}-connect \
  --config=config-management.yaml \
  --project=$PROJECT_ID

gcloud alpha container hub config-management status \
  --project=$PROJECT_ID