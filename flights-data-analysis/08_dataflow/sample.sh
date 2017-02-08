#!/bin/bash
DIR=/Users/vlakshmanan/data/flights
awk 'BEGIN {srand()} FNR > 1 { if (rand() <= .01) print $0}' $DIR/201501.csv > $DIR/small.csv
