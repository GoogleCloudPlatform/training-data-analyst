#!/bin/bash

MYSQLIP=$(gcloud sql instances describe flights | grep ipAddress | tr ' ' '\n' | tail -1)
mysql --host=$MYSQLIP --user=root --password --verbose < queries.sql

