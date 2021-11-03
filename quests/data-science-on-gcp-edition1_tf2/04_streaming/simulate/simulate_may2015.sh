#!/bin/bash
python3 simulate.py --project $(gcloud config get-value project) --startTime '2015-05-01 00:00:00 UTC' --endTime '2015-06-01 00:00:00 UTC' --speedFactor 30
