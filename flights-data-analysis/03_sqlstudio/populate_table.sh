#!/bin/bash

# To run mysqlimport and mysql, authorize CloudShell
gcloud sql instances patch flights --authorized-networks `bash find_my_ip.sh`

# Connect to MySQL using its IP address and do the import
MYSQLIP=$(gcloud sql instances describe flights | grep ipAddress | tr ' ' '\n' | tail -1)
mysql --host=$MYSQLIP --user=root --password --verbose < create_table.sql

# the table name for mysqlimport comes from the filename, so rename our CSV files
counter=0
for FILE in `ls ../data/*.csv`; do
   ln -sf $FILE flights.csv-${counter}
   counter=$((counter+1))
done

# import csv files
mysqlimport --local --host=$MYSQLIP --user=root --ignore-lines=1 --fields-terminated-by=',' --password bts flights.csv-*
rm flights.csv-* 

