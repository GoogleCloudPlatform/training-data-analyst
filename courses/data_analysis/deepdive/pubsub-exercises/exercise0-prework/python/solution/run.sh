#!/bin/bash
PROJECT=$(gcloud config get-value project)
python3 example.py -p $PROJECT -t pubsub-e2e-example -i ../../actions.csv -s pubsub-e2e-example-sub
