#!/bin/bash

if [ "$#" -ne 1 ]; then
   echo "Usage:   ./submit_workflow.sh bucket-name"
   exit
fi

TEMPLATE=ch6eph
MACHINE_TYPE=n1-standard-4
CLUSTER=ch6eph
BUCKET=$1

gsutil cp bayes_final.pig gs://$BUCKET/

gcloud dataproc --quiet workflow-templates delete $TEMPLATE
gcloud dataproc --quiet workflow-templates create $TEMPLATE

# the things we need pip-installed on the cluster
STARTUP_SCRIPT=gs://${BUCKET}/${CLUSTER}/startup_script.sh
echo "pip install --upgrade --quiet google-api-python-client" > /tmp/startup_script.sh
gsutil cp /tmp/startup_script.sh $STARTUP_SCRIPT

# create new cluster for job
gcloud dataproc workflow-templates set-managed-cluster $TEMPLATE \
    --master-machine-type $MACHINE_TYPE \
    --worker-machine-type $MACHINE_TYPE \
    --initialization-actions $STARTUP_SCRIPT \
    --num-preemptible-workers=3 --num-workers 2 \
    --image-version 1.4 \
    --cluster-name $CLUSTER

# steps in job
gcloud dataproc workflow-templates add-job \
  pig gs://$BUCKET/bayes_final.pig \
  --step-id create-report \
  --workflow-template $TEMPLATE \
  -- --bucket=$BUCKET
  
  
# submit workflow template
gcloud beta dataproc workflow-templates instantiate $TEMPLATE
