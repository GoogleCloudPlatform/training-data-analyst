#!/bin/bash
gcloud beta dataproc jobs submit pyspark --cluster cluster-1 eval.py
