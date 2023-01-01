#!/bin/bash -x

# Anthos Service Mesh setup with asmcli tool
# Uses legacy default ingress gateway for compatibility with older labs

# v.1.15
curl https://storage.googleapis.com/csm-artifacts/asm/asmcli_1.15 > asmcli
chmod +x asmcli

mkdir asm_output

./asmcli validate \
  --project_id $PROJECT_ID \
  --cluster_name $C1_NAME \
  --cluster_location $C1_ZONE \
  --fleet_id $PROJECT_ID \
  --output_dir ./asm_output

./asmcli install \
  --project_id $PROJECT_ID \
  --cluster_name $C1_NAME \
  --cluster_location $C1_ZONE \
  --fleet_id $PROJECT_ID \
  --output_dir ./asm_output \
  --enable_all \
  --ca mesh_ca

cat <<EOF | kubectl apply -f -
apiVersion: v1
data:
  mesh: |-
    defaultConfig:
      tracing:
        stackdriver:{}
kind: ConfigMap
metadata:
  name: istio-asm-managed
  namespace: istio-system
EOF

kubectl label namespace default istio-injection=enabled --overwrite
