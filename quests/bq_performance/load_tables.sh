#!/bin/bash
# populates the tables in dataset tpcds_*_flat_part_clust or dataset tpcds_*_nest_part_clust 
# dataset is hardcoded in the insert script specified by FILENAME

FILENAME="insert_flat_part_clust_tables.sql" # replace with name of sql script to run
IFS=";"
SECONDS=0
for stmt in $(<$FILENAME)　
do 
  echo "$stmt"
  `/Users/scohen/google-cloud-sdk/bin/bq query --nouse_legacy_sql $stmt` 
done
duration=$SECONDS
echo "$(($duration / 60)) minutes and $(($duration % 60)) seconds elapsed."