#!/bin/bash
# Change to your bucket
export BUCKET="[YOUR_GCS_BUCKET]"
cd ~/covid19
export today="$(date +"%Y-%m-%d")"
mkdir $today
cd $today
wget https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv
wget https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv
cd ..
gsutil cp -r "$today" gs://$BUCKET/covid19/
bq load --source_format=CSV --autodetect --replace \
	covid19.us_counties \
	gs://$BUCKET/covid19/"$today"/us-counties.csv
bq load --source_format=CSV --autodetect --replace \
	covid19.us_states \
	gs://$BUCKET/covid19/"$today"/us-states.csv
bq query <~/demo/covid19/create_views.sql
bq query <~/demo/covid19/materialize.sql
