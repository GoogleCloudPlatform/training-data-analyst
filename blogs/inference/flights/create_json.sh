#!/bin/bash

if [ "$#" -lt 1 ]; then
   echo "Usage:   ./run_oncloud.sh output_bucket_name "
   exit
fi

BUCKET=$1
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
python $DIR/csv_to_infapi.py \
  --input gs://cloud-training-demos/flights/tzcorr/all_flights* \
  --output_prefix gs://${BUCKET}/flights/json/sharded/flights_data \
  --runner DataflowRunner \
  --project $(gcloud config get-value project) \
  --staging_location gs://${BUCKET}/temp \
  --temp_location gs://${BUCKET}/temp \
  --job_name csvinfapi \
  --save_main_session \
  --max_num_workers 8 \
  --autoscaling_algorithm THROUGHPUT_BASED \
  --worker_machine_type n1-highmem-2
