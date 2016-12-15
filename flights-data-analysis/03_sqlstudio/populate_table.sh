#!/bin/bash

# To run mysqlimport and mysql, authorize CloudShell
bash authorize_cloudshell.sh

# the table name for mysqlimport comes from the filename, so rename our CSV files, changing bucket name as needed
counter=0
#for FILE in $(gsutil ls gs://cloud-training-demos-ml/flights/raw/2015*.csv); do
#   gsutil cp $FILE flights.csv-${counter}
for FILE in 201501.csv 201507.csv; do
   gsutil cp gs://cloud-training-demos-ml/flights/raw/$FILE flights.csv-${counter}
   counter=$((counter+1))
done

# import csv files
MYSQLIP=$(gcloud sql instances describe flights --format="value(ipAddresses.ipAddress)")
mysqlimport --local --host=$MYSQLIP --user=root --ignore-lines=1 --fields-terminated-by=',' --password bts flights.csv-*
rm flights.csv-* 

