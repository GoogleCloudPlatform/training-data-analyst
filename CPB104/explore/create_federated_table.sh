#!/bin/bash

TABLE=demos.test

bq rm $TABLE

# create a JSON description for table
bq mkdef 'gs://cloud-training-demos/sandiego/sensor_obs2008.csv' TIMESTAMP:timestamp,LATITUDE:float,LONGITUDE:float,FREEWAY_ID:string,FREEWAY_DIR:string,LANE:integer,SPEED:float | sed 's/ "skipLeadingRows": 0/ "skipLeadingRows": 1/g' > schema.json

bq mk --external_table_definition=schema.json $TABLE
