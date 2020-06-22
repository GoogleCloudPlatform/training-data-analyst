#!/bin/bash

argparse() {
if [ $# -ne 2 ]; then
    usage
fi
}

function usage {
   cat << EOF
Usage: test.sh <mode>

EOF
   exit 1
}

main() {
    echo $1
    argparse
    case $1 in

      local)
        export PROJECT_ID=$(gcloud config get-value project)
        export BUCKET=gs://${PROJECT_ID}
        export PIPELINE_FOLDER=${BUCKET}
        export MAIN_CLASS_NAME=com.mypackage.pipeline.BatchMinuteTrafficPipeline
        export RUNNER=DirectRunner
        export INPUT_PATH=../../events.json
        export TABLE_NAME=${PROJECT_ID}:logs.minute_traffic

        mvn compile exec:java \
        -Dexec.mainClass=${MAIN_CLASS_NAME} \
        -Dexec.cleanupDaemonThreads=false \
        -Dexec.args=" \
        --project=${PROJECT_ID} \
        --stagingLocation=${PIPELINE_FOLDER}/staging \
        --tempLocation=${PIPELINE_FOLDER}/temp \
        --runner=${RUNNER} \
        --inputPath=${INPUT_PATH} \
        --tableName=${TABLE_NAME}"
        ;;

      dataflow)
        export PROJECT_ID=$(gcloud config get-value project)
        export BUCKET=gs://${PROJECT_ID}
        export PIPELINE_FOLDER=${BUCKET}
        export MAIN_CLASS_NAME=com.mypackage.pipeline.BatchMinuteTrafficPipeline
        export RUNNER=DataflowRunner
        export INPUT_PATH=${PIPELINE_FOLDER}/events.json
        export TABLE_NAME=${PROJECT_ID}:logs.minute_traffic

        mvn compile exec:java \
        -Dexec.mainClass=${MAIN_CLASS_NAME} \
        -Dexec.cleanupDaemonThreads=false \
        -Dexec.args=" \
        --project=${PROJECT_ID} \
        --stagingLocation=${PIPELINE_FOLDER}/staging \
        --tempLocation=${PIPELINE_FOLDER}/temp \
        --runner=${RUNNER} \
        --inputPath=${INPUT_PATH} \
        --tableName=${TABLE_NAME}"
        ;;

    esac
}

main

