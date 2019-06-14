#!/bin/bash

# loads TPCDS data files into BQ tables using command-line bq

BQ_DIR=/Users/scohen/google-cloud-sdk/bin
data_files_listing=2t_data_files.txt   # file listing name 
bq_dataset=tpcds_2t_baseline           # BQ dataset name 

while IFS='' read -r mapping || [[ -n "$mapping" ]]; do
    echo "$mapping"
	`$BQ_DIR/bq load --field_delimiter '|' --ignore_unknown_values=true $bq_dataset.$mapping`
	echo "done loading file."
done < $data_files_listing


