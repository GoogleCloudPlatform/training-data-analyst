#!/bin/bash
echo ${YEAR:=2015}  # default if YEAR not set
for month in `seq -w 1 12`; do
    echo $YEAR$month.csv
    sed 's/,$//g' $YEAR$month.csv | sed 's/"//g' > tmp
    mv tmp $YEAR$month.csv
done
