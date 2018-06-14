#!/bin/bash
gcloud sql instances patch rentals \
    --authorized-networks `wget -qO - http://ipecho.net/plain`/32
