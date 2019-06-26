#!/bin/bash

# helper shell script to run multiple create table statements in bq
#
# before running: set the FILENAME and DATASET variables

FILENAME="EXAMPLE_flat_part_clust_tables.sql" # name of the sql script with the create table statements
DATASET="tpcds_2t_flat_part_clust" # name of the BQ dataset where to store the new tables
IFS=";"

echo "creating tables in dataset $DATASET."
`/Users/ldap/google-cloud-sdk/bin/bq rm -r -f $DATASET`
`/Users/ldap/google-cloud-sdk/bin/bq mk $DATASET`

for stmt in $(<$FILENAME)　
do 
  echo "$stmt"
  `/Users/ldap/google-cloud-sdk/bin/bq query --nouse_legacy_sql $stmt` 
done