#!/bin/bash


if [ "$#" -ne 1 ]; then
   echo "Usage:   ./submit_workflow.sh bucket-name"
   exit
fi

TEMPLATE=sparktobq
MACHINE_TYPE=n1-standard-4
CLUSTER=sparktobq
BUCKET=$1

gsutil cp spark_analysis.py gs://$BUCKET/

gcloud dataproc --quiet workflow-templates delete $TEMPLATE
gcloud dataproc --quiet workflow-templates create $TEMPLATE

# the things we need pip-installed on the cluster
STARTUP_SCRIPT=gs://${BUCKET}/sparktobq/startup_script.sh
echo "pip install --upgrade --quiet google-compute-engine google-cloud-storage matplotlib" > /tmp/startup_script.sh
gsutil cp /tmp/startup_script.sh $STARTUP_SCRIPT

# create new cluster for job
gcloud dataproc workflow-templates set-managed-cluster $TEMPLATE \
    --master-machine-type $MACHINE_TYPE \
    --worker-machine-type $MACHINE_TYPE \
    --initialization-actions $STARTUP_SCRIPT \
    --num-workers 2 \
    --image-version 1.4 \
    --cluster-name $CLUSTER

# steps in job
gcloud dataproc workflow-templates add-job \
  pyspark gs://$BUCKET/spark_analysis.py \
  --step-id create-report \
  --workflow-template $TEMPLATE \
  -- --bucket=$BUCKET
  
  
# submit workflow template
gcloud beta dataproc workflow-templates instantiate $TEMPLATE
