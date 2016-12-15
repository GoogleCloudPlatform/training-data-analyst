#!/bin/bash

# To run mysqlimport and mysql, authorize CloudShell
bash authorize_cloudshell.sh

# Connect to MySQL using its IP address and do the import
MYSQLIP=$(gcloud sql instances describe flights --format="value(ipAddresses.ipAddress)")
mysql --host=$MYSQLIP --user=root --password --verbose < create_table.sql
