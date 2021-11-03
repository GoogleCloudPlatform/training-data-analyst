#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: ./simulate.sh project-id"
    exit
fi

PROJECT=$1

cd ../04_streaming/simulate
python simulate.py --project $PROJECT --startTime "2015-04-01 00:00:00 UTC" --endTime "2015-04-03 00:00:00 UTC" --speedFactor 60 --jitter=None
