#!/bin/bash
for month in `seq -w 1 12`; do 
   unzip 2015$month.zip
   mv *ONTIME.csv 2015$month.csv
   rm 2015$month.zip
done
