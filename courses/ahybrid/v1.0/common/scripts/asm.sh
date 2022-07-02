# curl https://storage.googleapis.com/csm-artifacts/asm/asmcli_1.13 > asmcli

chmod +x ../common/scripts/asmcli

../common/scripts/asmcli \
--project_id $PROJECT_ID \
--cluster_name $C1_NAME \
--cluster_location $C1_ZONE \
--fleet_id $PROJECT_ID \
--output_dir . \
--enable_all \
--ca mesh_ca \
--custom_overlay $LAB_DIR/training-data-analyst/courses/ahybrid/v1.0/common/scripts/tracing.yaml

kubectl label namespace default \
  istio.io/rev=$(kubectl -n istio-system get pods -l app=istiod -o json | jq -r '.items[0].metadata.labels["istio.io/rev"]') \
  --overwrite