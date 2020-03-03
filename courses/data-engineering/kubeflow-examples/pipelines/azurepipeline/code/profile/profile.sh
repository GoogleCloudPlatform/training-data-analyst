#!/bin/sh
while getopts "m:n:i:d:s:p:u:r:w:t:b:" option;
    do
    case "$option" in
        m ) MODEL=${OPTARG};;
        n ) PROFILE_NAME=${OPTARG};;
        i ) INFERENCE_CONFIG=${OPTARG};;
        d ) DATA=${OPTARG};;
        s ) SERVICE_PRINCIPAL_ID=${OPTARG};;
        p ) SERVICE_PRINCIPAL_PASSWORD=${OPTARG};;
        u ) SUBSCRIPTION_ID=${OPTARG};;
        r ) RESOURCE_GROUP=${OPTARG};;
        w ) WORKSPACE=${OPTARG};;
        t ) TENANT_ID=${OPTARG};;
        b ) BASE_PATH=${OPTARG};;
    esac
done
az login --service-principal --username ${SERVICE_PRINCIPAL_ID} --password ${SERVICE_PRINCIPAL_PASSWORD} -t $TENANT_ID
az ml model profile -n $PROFILE_NAME -m ${MODEL}:1 --ic $INFERENCE_CONFIG -d $DATA -t myprofileresult.json -w $WORKSPACE -g $RESOURCE_GROUP
mv myprofileresult.json ${BASE_PATH}/myprofileresult.json
echo ${BASE_PATH}