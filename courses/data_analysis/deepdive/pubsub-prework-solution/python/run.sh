#!/bin/bash
PROJECT=`curl http://metadata.google.internal/computeMetadata/v1/project/project-id -H "Metadata-Flavor: Google"`
python3 example.py -p $PROJECT -t pubsub-e2e-example -i ../actions.csv -s pubsub-e2e-example-sub
