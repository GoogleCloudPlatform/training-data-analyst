#!/bin/bash -xe

metadata_value() {
  curl --retry 5 -sfH "Metadata-Flavor: Google" \
       "http://metadata/computeMetadata/v1/$1"
}

DEPLOYMENT_NAME=`metadata_value "instance/attributes/deployment"`

apt-get update
apt-get install -y git kubectl

# Add Bash completion for gcloud
echo 'source /usr/share/google-cloud-sdk/completion.bash.inc' >> /etc/profile

export PATH=$PATH:/usr/local/go/bin
export GOPATH=/root/go
export HOME=/root
cd ${HOME}

# Install Go
GO_VERSION=1.10.2
wget https://dl.google.com/go/go${GO_VERSION}.linux-amd64.tar.gz
tar -C /usr/local -xzf go${GO_VERSION}.linux-amd64.tar.gz
echo 'export PATH=$PATH:/usr/local/go/bin' >> /etc/profile

# Install hey https://github.com/rakyll/hey
go get -u github.com/rakyll/hey
cp /root/go/bin/hey /usr/local/bin

# Install Helm
HELM_VERSION=2.9.1
wget https://storage.googleapis.com/kubernetes-helm/helm-v${HELM_VERSION}-linux-amd64.tar.gz
tar zxfv helm-v${HELM_VERSION}-linux-amd64.tar.gz
cp linux-amd64/helm /usr/local/bin
cat > tiller-rbac.yaml <<EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: tiller
  namespace: kube-system
---
apiVersion: rbac.authorization.k8s.io/v1beta1
kind: ClusterRoleBinding
metadata:
  name: tiller
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
  - kind: ServiceAccount
    name: tiller
    namespace: kube-system
EOF

# Install kctx & kns
git clone https://github.com/ahmetb/kubectx
cp kubectx/kube* /usr/local/bin

# Prometheus resources to install in the clusters
wget -O prom-rbac.yml https://storage.googleapis.com/stackdriver-prometheus-documentation/rbac-setup.yml
wget https://storage.googleapis.com/stackdriver-prometheus-documentation/prometheus-service.yml

# Download Sock Shop App
curl --retry 5 -sfH "Metadata-Flavor: Google" \
     "http://metadata/computeMetadata/v1/instance/attributes/sock-shop" > sock-shop.yaml

WORKLOAD_FILTER="resourceLabels.purpose=workloads AND resourceLabels.deployment=${DEPLOYMENT_NAME}"
WORKLOAD_CLUSTERS=$(gcloud container clusters list --format 'csv[no-heading](name,zone)' --filter="${WORKLOAD_FILTER}")
for CLUSTER_INFO in ${WORKLOAD_CLUSTERS}; do
    CLUSTER_INFO_ARRAY=(${CLUSTER_INFO//,/ })

    # Wait until cluster is running
    until gcloud container clusters describe ${CLUSTER_INFO_ARRAY[0]} --zone ${CLUSTER_INFO_ARRAY[1]} --format 'value(status)' | grep -m 1 "RUNNING"; do sleep 10 ; done

    # Get credentials for setting client as admin
    gcloud container clusters get-credentials ${CLUSTER_INFO_ARRAY[0]} --zone ${CLUSTER_INFO_ARRAY[1]}
    kubectl create clusterrolebinding client-cluster-admin-binding --clusterrole=cluster-admin --user=client
    # Needed for Spinnaker to be able to authenticate to the API
    export CLOUDSDK_CONTAINER_USE_CLIENT_CERTIFICATE=True
    gcloud container clusters get-credentials ${CLUSTER_INFO_ARRAY[0]} --zone ${CLUSTER_INFO_ARRAY[1]}

    # Install Prometheus
    export PROJECT=$(gcloud info --format='value(config.project)')
    kubectl apply -f prom-rbac.yml --as=admin --as-group=system:masters
    cp prometheus-service.yml prom-${CLUSTER_INFO_ARRAY[0]}.yml
    sed -i "s/_stackdriver_project_id: .*/_stackdriver_project_id: '${PROJECT}'/g" prom-${CLUSTER_INFO_ARRAY[0]}.yml
    sed -i "s/_kubernetes_cluster_name: .*/_kubernetes_cluster_name: '${CLUSTER_INFO_ARRAY[0]}'/g" prom-${CLUSTER_INFO_ARRAY[0]}.yml
    sed -i "s/_kubernetes_location: .*/_kubernetes_location: '${CLUSTER_INFO_ARRAY[1]}'/g" prom-${CLUSTER_INFO_ARRAY[0]}.yml
    kubectl apply -f prom-${CLUSTER_INFO_ARRAY[0]}.yml

    kubectl apply -f tiller-rbac.yaml
    helm init --service-account tiller
    # Wait for tiller to be running
    sleep 60

    # Install Istio
    ISTIO_VERSION=0.8.0
    curl -L https://git.io/getLatestIstio | sh -
    pushd istio-${ISTIO_VERSION}/
    helm install -n istio --namespace=istio-system --set sidecar-injector.enabled=true install/kubernetes/helm/istio
    popd
    kubectl label namespace default istio-injection=enabled
done

SOCKSHOP_FILTER="resourceLabels.purpose=workloads AND resourceLabels.deployment=${DEPLOYMENT_NAME} AND resourceLabels.sock-shop=installed"
SOCKSHOP_CLUSTERS=$(gcloud container clusters list --format 'csv[no-heading](name,zone)' --filter="${SOCKSHOP_FILTER}")
for CLUSTER_INFO in ${SOCKSHOP_CLUSTERS}; do
    CLUSTER_INFO_ARRAY=(${CLUSTER_INFO//,/ })
    # Wait until cluster is running
    until gcloud container clusters describe ${CLUSTER_INFO_ARRAY[0]} --zone ${CLUSTER_INFO_ARRAY[1]} --format 'value(status)' | grep -m 1 "RUNNING"; do sleep 10 ; done
    gcloud container clusters get-credentials ${CLUSTER_INFO_ARRAY[0]} --zone ${CLUSTER_INFO_ARRAY[1]}

    kubectl apply -f sock-shop.yaml
done

# Configure Spinnaker
SPINNAKER_FILTER="resourceLabels.purpose=spinnaker AND resourceLabels.deployment=${DEPLOYMENT_NAME}"
SPINNAKER_CLUSTERS=$(gcloud container clusters list --format 'csv[no-heading](name,zone)' --filter="${SPINNAKER_FILTER}")
for CLUSTER_INFO in ${SPINNAKER_CLUSTERS}; do
    CLUSTER_INFO_ARRAY=(${CLUSTER_INFO//,/ })
    gcloud container clusters get-credentials ${CLUSTER_INFO_ARRAY[0]} --zone ${CLUSTER_INFO_ARRAY[1]}
    kubectl apply -f tiller-rbac.yaml
    helm init --service-account tiller
    # Wait for tiller to be running
    sleep 60

    # Create Spinnaker service account and assign it storage.admin role.
    gcloud iam service-accounts create spinnaker-sa-${DEPLOYMENT_NAME} --display-name spinnaker-sa-${DEPLOYMENT_NAME}
    export SPINNAKER_SA_EMAIL=$(gcloud iam service-accounts list \
        --filter="displayName:spinnaker-sa-${DEPLOYMENT_NAME}" \
        --format='value(email)')
    export PROJECT=$(gcloud info --format='value(config.project)')

    # Move this to DM template
    gcloud projects add-iam-policy-binding ${PROJECT} --role roles/storage.admin --member serviceAccount:${SPINNAKER_SA_EMAIL}
    gcloud iam service-accounts keys create spinnaker-key.json --iam-account ${SPINNAKER_SA_EMAIL}
    export BUCKET=${PROJECT}-${DEPLOYMENT_NAME}
    gsutil mb -c regional -l us-west1 gs://${BUCKET}

    # Use upstream once this PR is merged: https://github.com/kubernetes/charts/pull/5456
    git clone https://github.com/viglesiasce/charts -b mcs
    pushd charts/stable/spinnaker
    helm dep build
    popd

    kubectl create secret generic --from-file=config=${HOME}/.kube/config my-kubeconfig

    export SA_JSON=$(cat spinnaker-key.json)
    cat > spinnaker-config.yaml <<EOF
storageBucket: ${BUCKET}
kubeConfig:
  enabled: true
  secretName: my-kubeconfig
  secretKey: config
  contexts:
  - gke_${PROJECT}_us-west1-c_${DEPLOYMENT_NAME}-west
  - gke_${PROJECT}_us-east4-b_${DEPLOYMENT_NAME}-east
gcs:
  enabled: true
  project: ${PROJECT}
  jsonKey: '${SA_JSON}'

# Disable minio the default
minio:
  enabled: false

# Configure your Docker registries here
accounts:
- name: gcr
  address: https://gcr.io
  username: _json_key
  password: '${SA_JSON}'
  email: 1234@5678.com
EOF
    helm install -n adv-k8s charts/stable/spinnaker -f spinnaker-config.yaml --timeout 600
done
