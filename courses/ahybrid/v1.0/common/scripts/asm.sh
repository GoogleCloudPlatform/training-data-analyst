# curl https://storage.googleapis.com/csm-artifacts/asm/install_asm_1.9 > install_asm

chmod +x ../common/scripts/install_asm

../common/scripts/install_asm \
--project_id $PROJECT_ID \
--cluster_name $C1_NAME \
--cluster_location $C1_ZONE \
--mode install \
--enable_gcp_apis \
--enable_all \
--custom_overlay $LAB_DIR/training-data-analyst/courses/ahybrid/v1.0/common/scripts/tracing.yaml

kubectl label namespace default \
  istio.io/rev=$(kubectl -n istio-system get pods -l app=istiod -o json | jq -r '.items[0].metadata.labels["istio.io/rev"]') \
  --overwrite