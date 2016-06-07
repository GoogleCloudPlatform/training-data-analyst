#!/bin/bash
for month in `seq -w 1 12`; do
    echo 2015$month.csv
    sed 's/,$//g' ~/data/flights/2015$month.csv | sed 's/"//g' > tmp
    mv tmp 2015$month.csv
done
