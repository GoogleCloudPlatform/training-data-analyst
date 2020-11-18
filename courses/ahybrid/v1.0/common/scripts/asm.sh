curl --request POST \
  --header "Authorization: Bearer $(gcloud auth print-access-token)" \
  --data '' \
  https://meshconfig.googleapis.com/v1alpha1/projects/${PROJECT_ID}:initialize


curl -LO https://storage.googleapis.com/gke-release/asm/istio-1.6.8-asm.9-linux-amd64.tar.gz
tar xzf istio-1.6.8-asm.9-linux-amd64.tar.gz
cd istio-1.6.8-asm.9
export PATH=$PWD/bin:$PATH

kpt pkg get https://github.com/GoogleCloudPlatform/anthos-service-mesh-packages@1.6.8-asm.9 asm

cd asm
kpt cfg set asm gcloud.container.cluster ${C1_NAME}
kpt cfg set asm gcloud.project.environProjectNumber ${PROJECT_NUMBER}
kpt cfg set asm gcloud.core.project ${PROJECT_ID}
kpt cfg set asm gcloud.compute.location ${C1_ZONE}

# To configure that all clusters are in the same project
kpt cfg set asm anthos.servicemesh.profile asm-gcp

gcloud container clusters get-credentials $C1_NAME \
    --zone $C1_ZONE --project $PROJECT_ID

# Install Istio + Enable tracing with Cloud Trace
istioctl install -f asm/cluster/istio-operator.yaml -f $LAB_DIR/training-data-analyst/courses/ahybrid/v1.0/AHYBRID050/scripts/tracing.yaml

# Enable the Anthos Service Mesh UI in Cloud Console
kubectl apply -f asm/canonical-service/controller.yaml

kubectl wait --for=condition=available --timeout=600s deployment \
  --all -n istio-system

