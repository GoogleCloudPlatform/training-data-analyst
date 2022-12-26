#! /bin/sh
export BUCKET=gs://$GOOGLE_CLOUD_PROJECT
export REGION=us-central1
python spanner-to-bq.py --temp_location gs://$BUCKET/tmp/ --region $REGION --project $GOOGLE_CLOUD_PROJECT --runner DataflowRunner

