# az ml model deploy -n tacosandburritos -m tacosandburritos:1 --ic inferenceconfig.json --dc deploymentconfig.json --resource-group taco-rg --workspace-name taco-workspace --overwrite -v
#!/bin/sh
while getopts "m:n:i:d:s:p:u:r:w:t:b:" option;
    do
    case "$option" in
        m ) MODEL=${OPTARG};;
        n ) MODEL_NAME=${OPTARG};;
        i ) INFERENCE_CONFIG=${OPTARG};;
        d ) DEPLOYMENTCONFIG=${OPTARG};;
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
az ml model deploy -n $MODEL_NAME -m ${MODEL}:1 --ic $INFERENCE_CONFIG --pi ${BASE_PATH}/myprofileresult.json --dc $DEPLOYMENTCONFIG -w $WORKSPACE -g $RESOURCE_GROUP --overwrite -v