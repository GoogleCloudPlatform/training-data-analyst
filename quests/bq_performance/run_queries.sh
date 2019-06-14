#!/bin/bash
# runs 38 queries from the benchmark 

FILENAME="EXAMPLE_nest_part_clust_queries.sql" # replace with name of sql script to run
LOGFILE="nest_part_clust_queries.log"  # replace with name of log file to write
IFS=";"

start=$(date +%s)
index=0
for stmt in $(<$FILENAME)　
do 
  echo $stmt
  echo $stmt >> $LOGFILE
  
  SECONDS=0
  `/Users/scohen/google-cloud-sdk/bin/bq query --nouse_legacy_sql $stmt` 
  duration=$SECONDS
  
  index=$((index+1))
  echo "Query $index ran in $(($duration / 60)) minutes and $(($duration % 60)) seconds."
  echo "Query $index ran in $(($duration / 60)) minutes and $(($duration % 60)) seconds." >> $LOGFILE
done

end=$(date +%s)
elapsed_seconds=$(echo "$end - $start" | bc)
echo "$(($elapsed_seconds / 60)) minutes and $(($elapsed_seconds % 60)) seconds elapsed."