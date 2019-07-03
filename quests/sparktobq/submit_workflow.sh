#!/bin/bash

TEMPLATE=sparktobq
MACHINE_TYPE=n1-highcpu-4
CLUSTER=sparktobq
BUCKET=cloud-training-demos-ml

gcloud dataproc workflow-templates delete $TEMPLATE
gcloud dataproc workflow-templates create $TEMPLATE

# the things we need pip-installed on the cluster
STARTUP_SCRIPT=gs://${BUCKET}/sparktobq/startup_script.sh
echo "pip install --upgrade --quiet google-compute-engine google-cloud-storage" > /tmp/startup_script.sh
gsutil cp /tmp/startup_script.sh $STARTUP_SCRIPT

# create new cluster for job
gcloud dataproc workflow-templates set-managed-cluster $TEMPLATE \
    --master-machine-type $MACHINE_TYPE \
    --worker-machine-type $MACHINE_TYPE \
    --initialization-actions $STARTUP_SCRIPT \
    --num-workers 2 \
    --image-version 1.14 \
    --cluster-name $CLUSTER

# steps in job
gcloud dataproc workflow-templates add-job \
  pyspark spark_analysis.py \
  --step-id create-report \
  --workflow-template $TEMPLATE \
  -- --bucket=$BUCKET
  
  
# submit workflow template
gcloud beta dataproc workflow-templates instantiate $TEMPLATE