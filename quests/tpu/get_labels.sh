#!/bin/bash

gsutil cat gs://cloud-ml-data/img/flower_photos/train_set.csv  | sed 's/,/ /g' | awk '{print $2}' | sort | uniq
