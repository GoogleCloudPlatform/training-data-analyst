#!/bin/bash
gcloud beta pubsub subscriptions pull testsubscription | tr ' ' '\n' | grep objectId
