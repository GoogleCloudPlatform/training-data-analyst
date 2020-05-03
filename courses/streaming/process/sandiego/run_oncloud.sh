#!/bin/bash

if [ "$#" -lt 3 ]; then
   echo "Usage:   ./run_oncloud.sh project-name bucket-name AverageSpeeds  [options] "
   echo "Example: ./run_oncloud.sh cloud-training-demos cloud-training-demos CurrentConditions --bigtable"
   exit
fi

PROJECT=$qwiklabs-gcp-00-69692f620cf4
shift
BUCKET=$qwiklabs-gcp-00-69692f620cf4
shift
MAIN=com.google.cloud.training.dataanalyst.sandiego.$1
shift

echo "Launching $MAIN project=$PROJECT bucket=$BUCKET $*"

export PATH=/usr/lib/jvm/java-8-openjdk-amd64/bin/:$PATH
mvn compile -e exec:java \
 -Dexec.mainClass=$MAIN \
      -Dexec.args="--project=$PROJECT \
      --stagingLocation=gs://$BUCKET/staging/ $* \
      --tempLocation=gs://$BUCKET/staging/ \
      --runner=DataflowRunner"


# If you run into quota problems, add this option the command line above
#     --maxNumWorkers=2 
# In this case, you will not be able to view autoscaling, however.
