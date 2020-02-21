# Python scripts to access BigQuery Services
Python Version : 3.7

## Note :
- Each of the below script is an improvement on the previous one
- For non parameterized implementations bq(1 through 11), manually set the _CREDFILE variable pointing to your service account credential json file
- If no log setting is specified. Defaults to Debug mode, stdout, logs/[YYYYMMDD]_bqclient.log as log target in current folder


## Install Dependencies


1)  Install ```pip```_ and ```virtualenv```_ if you do not already have them.
   You may want to refer to the ```Python Development Environment Setup Guide``` for Google Cloud Platform for instructions.

  Python Development Environment Setup Guide:
  https://cloud.google.com/python/setup

2) Cd to project folder

3) Create a virtualenv.

    ```
    $ virtualenv --python python3 env
    $ source env/bin/activate
    ```

4) Install the dependencies needed to run the samples.

    `$ pip install -r requirements.txt`

Now the environment is ready !

* pip: https://pip.pypa.io/
* virtualenv: https://virtualenv.pypa.io/
* Google Cloud SDK: https://cloud.google.com/sdk/


### bq1_default_auth_and_log.py

- Executes a predefined query against a public bigquery data set and prints every row using the default python logger
- Uses an env variable to authenticate the bigquery client
- Make sure to set the env variable GOOGLE_APPLICATION_CREDENTIALS pointing to credential file for a service account
- More details Google's Application Default Credentials Strategy(ADC) strategy : https://cloud.google.com/docs/authentication/production
- Change the variable  _QUERY  in init_query_text() for custom query

Note: This is the skeleton script for all the subsequent implementations. Change each function as per requirement.

```
Usage : python bq1_default_auth_and_log.py
```


### bq2_improved_auth.py

- Uses a predefined credential file path from a global variable and a scope as input credentials to authenticate the bigquery client
- Make sure to set the credential file path for the global variable _CREDFILE

```
Usage : python bq2_improved_auth.py
```


### bq3_sysoutlog.py

- Improved Logging : Custom formatter for stdout stream handler for logging

```
Usage : python bq3_sysoutlog.py
```


### bq4_jsonlog_stdout.py

- Structured Json Logging : CustomJsonformatter for stdout stream handler
- Improved Qyery Result handling : Added generic logic for column-value dict instead of explicilty mentioning each
- Added metadata for every log record

```
usage : python bq4_jsonlog_stdout.py
```


### bq5_jsonlog_file.py
- Structured Json Logging : CustomJsonformatter for File stream handler
- Change the CustomJsonFormatter class as per requirement

```
usage : python bq5_jsonlog_file.py
```



### bq6_jsonlog_stackdriver.py

- Structured Json Logging : CustomJsonformatter for Stackdriver Stream handler

```
usage : python bq6_jsonlog_stackdriver.py
```



### bq7_jsonlog_stackdriverandfile.py

- Structured Json Logging : CustomJsonformatter for Stackdriver and File Stream handler
- This implementation gives an idea about how to club different log handlers together. Modify as per need.

```
usage : python bq7_jsonlog_stackdriverandfile.py
```



### bq8_queryfile.py

- Added support for reqding a query from file
- Update the global variable _QUERY_FILE with your query file or it will use the default in the resources/query1.sql file

```
Usage : python bq8_queryfile.py
```


### bq9_queryparams.py

- Adding support for named and positional query parameters
- Reference :https://cloud.google.com/bigquery/docs/parameterized-queries

- For named params, use the following in script
``` 
_QUERY_FILE = "resources/query_named_params.sql"
_QUERY_PARAMS = "[('tags','STRING','%google-bigquery%'), ('limit','INT64',10)]"
```

- For positional params, use the following in script

``` 
 _QUERY_FILE = "resources/query_positional_params.sql"
 _QUERY_PARAMS = "[(None,'STRING','%google-bigquery%'), (None,'INT64',10)]"
```


```
usage : bq9_queryparams.py
```



### bq10_query_dryrun_cache.py

- Adding support for runnign the query in dry run mode and also added query cache flag
- Change the global variable : _DRY_RUN_FLAG = True/False, _QUERY_CACHE_FLAG = True/False

```
usage : python bq10_query_dryrun_cache.py
```



### bq11_job_query_stats.py

- Adding support stats for query runtime and script runtimes
- Script params is logged at the end of the main function
- Query params : seperate function log_query_stats()
- Usage :
```
 python bq11_job_query_stats.py
```



### bq12_parameterized.py

- This is parameterized version of all the features of previous implementations.

```
usage: bq12_parameterized.py [-h] [--project-id PROJECT_ID]
                             [--dry-run DRY_RUN] [--query-cache QUERY_CACHE]
                             [--query-params QUERY_PARAMS]
                             [--credfile CREDFILE] [--query QUERY]
                             [--queryfile QUERYFILE] [--logtarget LOGTARGET]
                             [--logger-name LOGGER_NAME] [--logfile LOGFILE]
                             [--loglevel LOGLEVEL]
```

Use the -h flag for more details on the paramaters

#### Examples :
##### Positional Params
```
bq_parameterized.py \
            --query-params "[(None,'STRING','%google-bigquery%'), (None,'INT64',10)]" \
            --queryfile resources/query_positional_params.sql \
            --credfile credentials/service_account.json \
            --loglevel debug \
            --logtarget stackdriverandfile
```


##### Named Query Parmams
```
Usage : python bq12_parameterized.py \
               --query-params "[('tags','STRING','%google-bigquery%'), ('limit','INT64',10)]" \
               --queryfile resources/query_named_params.sql \
               --credfile credentials/service_account.json \
               --loglevel debug \
               --logtarget stackdriverandfile
```



### bq13_queryasync.py

- Multiprocessing support to execute queries asynchronously.
- Reference : https://docs.python.org/3/library/concurrent.futures.html#processpoolexecutor
- Note : Make sure the query_params and values for every query in the bulk set defined in the function run_bulk_asyn_queries() match that of the input query
- Params added in comparision to previous implementation bq12_parameterized
 ``` 
      [--query-mode QUERY_MODE]
      [--max-processes MAX_PROCESSES]
      [--query-range-start QUERY_RANGE_START]
      [--query-range-end QUERY_RANGE_END]
```

- Usage:
```
bq13_queryasync.py [-h] [--project-id PROJECT_ID] [--dry-run DRY_RUN]
                          [--query-cache QUERY_CACHE]
                          [--query-mode QUERY_MODE]
                          [--max-processes MAX_PROCESSES]
                          [--query-range-start QUERY_RANGE_START]
                          [--query-range-end QUERY_RANGE_END]
                          [--query-params QUERY_PARAMS] [--credfile CREDFILE]
                          [--query QUERY] [--queryfile QUERYFILE]
                          [--logtarget LOGTARGET] [--logger-name LOGGER_NAME]
                          [--logfile LOGFILE] [--loglevel LOGLEVEL]
```

        Use the -h flag for more details on the paramaters

####Example
##### create table :
```
python bq13_queryasync.py --queryfile resources/create_partitionedtable.sql
```

#####async insert :
```
python bq13_queryasync.py \
                --queryfile resources/insert_dml.sql \
                --query-mode async \
                --query-range-start 1 \
                --query-range-end 1000 \
                --max-processes 15
```

### bq14_gcs_bqload.py
- Parameterized bigquery script to upload files to given gcs path and load into a bigquery table
- Autocreates gcs bucket if not present
- Autocreates Bigquery table with autodetecting schema from input file and name as given input name
- Currently Truncates data into the biguqery table (Modify as per need)
- Script params added :
```
  [--gcs-path GCS_PATH]  Gcs path where the file needs to be uploaded
  [--upload-file UPLOAD_FILE] Input file path to be uploaded to gcs
  [--bqtable-name BQTABLE_NAME] Bigquery Table name into which the data is loaded
```

- If bqtable-name is not passed, the given file is loaded to gcs and no load job is initiated

- Usage:
```
  bq14_gcs_bqload.py [-h] [--project-id PROJECT_ID] [--dry-run DRY_RUN]
                          [--query-cache QUERY_CACHE]
                          [--query-mode QUERY_MODE]
                          [--max-processes MAX_PROCESSES]
                          [--query-range-start QUERY_RANGE_START]
                          [--query-range-end QUERY_RANGE_END]
                          [--query-params QUERY_PARAMS] [--credfile CREDFILE]
                          [--query QUERY] [--queryfile QUERYFILE]
                          [--logtarget LOGTARGET] [--logger-name LOGGER_NAME]
                          [--logfile LOGFILE] [--loglevel LOGLEVEL]
                          [--gcs-path GCS_PATH] [--upload-file UPLOAD_FILE]
                          [--bqtable-name BQTABLE_NAME]
```

####Example
```
 python bq14_gcs_bqload.py \
        --gcs-path gs://nikunj-bq-gcs/uploads/flatfiles/ \
        --upload-file resources/flatfiles/test-file.csv  \
        --bqtable-name bqtestdataset.test_load_table
```

### bq15_authorized_views.py
- Added support to authorize all / selective views to access the source dataset
- In order to provide the service account access to both the projects (source and shared), copy the "client_email" key value from service account file
  and add an IAM policy Bigquery.dataViewer for this user in the shared dataset project
- The argument ids need to be fully-qualified ID in standard SQL format :
   ```
      dataset : <project_name>.<dataset_name>
      view    : <project_name>.<dataset_name>.<table_name>
   ```
- Either one of the two args : shared_dataset_id or shared_view_id is manditory
    - If shared_dataset_id is given, the script scans through all the tables in the given dataset and authorizes all the views to access the source dataset
    - If shared_view_id is given, the script just authorized the given view to access the source dataset
- Handles duplicate access entries i.e pre authorized views in a given dataset are ignored
- Lists a max of 1000000 tables in a given dataset. Increase the value of max_results in the function get_all_dataset_views if required
- Script params added :
```
   [--authview-source-datasetid AUTHVIEW_SOURCE_DATASETID]
   [--authview-shared-datasetid AUTHVIEW_SHARED_DATASETID]
   [--authview-shared-viewid AUTHVIEW_SHARED_VIEWID]
```

- Usage :
```
usage: bq15_authorized_views.py [-h] [--project-id PROJECT_ID]
                                [--dry-run DRY_RUN]
                                [--query-cache QUERY_CACHE]
                                [--query-mode QUERY_MODE]
                                [--max-processes MAX_PROCESSES]
                                [--query-range-start QUERY_RANGE_START]
                                [--query-range-end QUERY_RANGE_END]
                                [--query-params QUERY_PARAMS]
                                [--credfile CREDFILE] [--query QUERY]
                                [--queryfile QUERYFILE]
                                [--logtarget LOGTARGET]
                                [--logger-name LOGGER_NAME]
                                [--logfile LOGFILE] [--loglevel LOGLEVEL]
                                [--gcs-path GCS_PATH]
                                [--upload-file UPLOAD_FILE]
                                [--bqtable-name BQTABLE_NAME]
                                [--authview-source-datasetid AUTHVIEW_SOURCE_DATASETID]
                                [--authview-shared-datasetid AUTHVIEW_SHARED_DATASETID]
                                [--authview-shared-viewid AUTHVIEW_SHARED_VIEWID]
```

#### Example :
##### With source and shared datasets :
```
python bq15_authorized_views.py \
    --authview-source-datasetid nikunjbhartia-test-clients.bqtestdataset \
    --authview-shared-datasetid nikunjbhartia-sce-testenv.bqtest
```

##### With source dataset and a selective shared view :
```
python bq15_authorized_views.py \
    --authview-source-datasetid nikunjbhartia-test-clients.bqtestdataset \
    --authview-shared-viewid nikunjbhartia-sce-testenv.bqtest.github_authors
```

### bq16_external_bigtable.py
- Added support for creating a permanent external Bigquery table pointing to an existing Bigtable table.
- Option to create either external BQ table either for a given BT table or for all tables in a given BT instanceid
- All the columns will be read as string with the BT readLatestflag turned on
- Default batch sample batch size is 1 i.e. script will read the first row and decide the schema for the BQ table
- If no data is found in the source BT table, then creation of external BQ table is aborted.
- Ensure your BT instance and BQ dataset lie in the same project and are in the regions specified here : https://cloud.google.com/bigquery/external-data-sources
- Name of the external BQ table will be same as that of the corressponding BT table
- If a table with same name is already there in the given BQ dataset, it overrides with the current derived schema (as per batch size)

- Script params added :
```
  --bt-instance-id BT_INSTANCE_ID  Source BT instance id 
  --bt-table-id BT_TABLE_ID  Source BT table id (mention either this or the instance id for full table list)
  --bq-dataset-id BQ_DATASET_ID  Target BQ datasetid in the same project for creating the external BQ tables pointing to BT                    
  --bt-sample-batch BT_SAMPLE_BATCH  Number of rows to be sampled for schema derivation from a BT table
```
- Usage :
```
usage: bq16_external_bigtable.py [-h] [--project-id PROJECT_ID]
                                 [--dry-run DRY_RUN]
                                 [--query-cache QUERY_CACHE]
                                 [--query-mode QUERY_MODE]
                                 [--max-processes MAX_PROCESSES]
                                 [--query-range-start QUERY_RANGE_START]
                                 [--query-range-end QUERY_RANGE_END]
                                 [--query-params QUERY_PARAMS]
                                 [--credfile CREDFILE] [--query QUERY]
                                 [--queryfile QUERYFILE]
                                 [--logtarget LOGTARGET]
                                 [--logger-name LOGGER_NAME]
                                 [--logfile LOGFILE] [--loglevel LOGLEVEL]
                                 [--gcs-path GCS_PATH]
                                 [--upload-file UPLOAD_FILE]
                                 [--bqtable-name BQTABLE_NAME]
                                 [--authview-source-datasetid AUTHVIEW_SOURCE_DATASETID]
                                 [--authview-shared-datasetid AUTHVIEW_SHARED_DATASETID]
                                 [--authview-shared-viewid AUTHVIEW_SHARED_VIEWID]
                                 [--bt-instance-id BT_INSTANCE_ID]
                                 [--bt-table-id BT_TABLE_ID]
                                 [--bt-sample-batch BT_SAMPLE_BATCH]
                                 [--bq-dataset-id BQ_DATASET_ID]
```
### Example :
#### With source BT instanceId and target BQ datasetId (will create all tables)
```
python bq16_external_bigtable.py \
    --bt-table-id financial_data \
    --bt-sample-batch 10 
    --bt-instance-id bigtable-us-instance 
    --bq-dataset-id us_dataset 
    --credfile <path to your service account key file>
```

#### With source BT instanceId and tableId and target BQ datasetId 
```
python bq16_external_bigtable.py \
    --bt-sample-batch 10 
    --bt-instance-id bigtable-us-instance 
    --bq-dataset-id us_dataset 
    --credfile <path to your service account key file>
```

### JSON Service account Credential File Example

Note : Structure as of 2019 Oct 18. Subject to change
Reference link for creating the file : https://cloud.google.com/iam/docs/creating-managing-service-account-keys#iam-service-account-keys-create-console

```
{
  "type": "service_account",
  "project_id": "<project-name>",
  "private_key_id": "<private-key-id>",
  "private_key": "<private-key>",
  "client_email": "<client-email>",
  "client_id": "<client-id>",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "h<certs-uri>"
}
```



