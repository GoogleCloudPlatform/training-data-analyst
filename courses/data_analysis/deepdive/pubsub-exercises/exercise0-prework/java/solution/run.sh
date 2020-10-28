#!/bin/bash
PROJECT=$(gcloud config get-value project)
java -Xmx1024m -cp target/pubsub-prework.jar com.google.cloud.sme.pubsub.Example -p $PROJECT -t pubsub-e2e-example -i ../../actions.csv -s pubsub-e2e-example-sub
