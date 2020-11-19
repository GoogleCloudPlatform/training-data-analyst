curl https://storage.googleapis.com/csm-artifacts/asm/install_asm_1.7 > install_asm

chmod +x install_asm
./install_asm \
--project_id $PROJECT_ID \
--cluster_name $C1_NAME \
--cluster_location $C1_ZONE \
--mode install \
--enable_apis \
--customer_overlay $LAB_DIR/training-data-analyst/courses/ahybrid/v1.0/AHYBRID050/scripts/tracing.yaml