#!/bin/bash

bash authorize_cloudshell.sh
MYSQLIP=$(gcloud sql instances describe flights | grep ipAddress | tr ' ' '\n' | tail -1)
cat contingency.sql | sed 's/DEP_DELAY_THRESH/20/g' | sed 's/ARR_DELAY_THRESH/15/g' | mysql --host=$MYSQLIP --user=root --password --verbose

