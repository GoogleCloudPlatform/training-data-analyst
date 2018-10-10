#!/bin/bash
PROJECT=`curl http://metadata.google.internal/computeMetadata/v1/project/project-id -H "Metadata-Flavor: Google"`
java -Xmx1024m -cp target/pubsub-prework.jar com.google.cloud.sme.pubsub.Example -p $PROJECT -t pubsub-e2e-example -i ../actions.csv -s pubsub-e2e-example-sub
