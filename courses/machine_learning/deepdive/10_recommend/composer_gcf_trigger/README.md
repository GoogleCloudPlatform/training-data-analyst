## Cloud Composer workflow using Cloud Dataflow
##### This notebook contains an example Cloud Composer workflow that triggers Cloud Dataflow to transform, enrich and load a delimited text file into Cloud BigQuery.
The goal of this example is to provide a common pattern to automatically trigger, via Google Cloud Function, a Dataflow job when a file arrives in Google Cloud Storage, process the data and load it into BigQuery.

### Workflow Overview 

***

![Alt text](img/workflow-overview.png "Workflow Overview")
A Cloud Function with a Cloud Storage trigger is used to initiate the workflow when a file is uploaded for processing.

At a high-level the Cloud Composer workflow performs the following steps:
1. Extracts the location of the input file that triggered the workflow.
2. Executes a Cloud Dataflow job that performs the following:
    - Parses the delimited input file and adds some useful 'metadata'
        - 'filename': The name of the file that is proceeded by the Cloud Dataflow job
        - 'load_dt': The date in YYYY-MM-DD format when the file is processed
    - Loads the data into an existing Cloud BigQuery table (any existing data is truncated)
3. Moves the input file to a Cloud Storage bucket that is setup for storing processed files.

##### 1. Extract the input file location:
When a file is uploaded to the Cloud Storage bucket, a Cloud Function is triggered. This invocation wraps the event information (_bucket and object details_) that triggered this event and passes it to the the Cloud Composer workflow that gets triggered. The workflow extracts this information and passes it to the Cloud Dataflow job.
```
job_args = {
        'input': 'gs://{{ dag_run.conf.get("bucket") }}/{{ dag_run.conf.get("name") }}',
        'output': models.Variable.get('bq_output_table'),
        'fields': models.Variable.get('input_field_names'),
        'load_dt': ds_tag
    }
```

##### 2. Executes the Cloud Dataflow job

The workflow then executes a [Cloud Dataflow job](dataflow/process_delimited.py) to process the delimited file, adds filename and load_dt fields and loads the data into a Cloud BigQuery table.

##### 3. Move to processed bucket


![Alt text](img/sample-dag.png "DAG Overview")

Based on the status of the Cloud Dataflow job, the workflow will then move the processed files to a Cloud Storage bucket setup to store processed data. A separate folder is created along with a processed date field to hold the files in this bucket.

##### Full code examples

Ready to dive deeper? Check out the complete code [here](simple_load_dag.py)

***

#### Setup and Pre-requisites
It is recommended that virtualenv be used to keep everything tidy. The [requirements.txt](requirements.txt) describes the dependencies needed for the code used in this repo.

The following high-level steps describe the setup needed to run this example:

1. Create a Cloud Storage (GCS) bucket for receiving input files (*input-gcs-bucket*).
2. Create a GCS bucket for storing processed files (*output-gcs-bucket*).
3. Create a Cloud Composer environment - Follow [these](https://cloud.google.com/composer/docs/quickstart) steps to create a Cloud Composer environment if needed (*cloud-composer-env*).
4. Create a Cloud BigQuery table for the processed output. The following schema is used for this example:

|Column Name | Column Type|
|:-----------|:-----------|
|state	     |STRING      |
|gender	     |STRING      |
|year	     |STRING      |
|name	     |STRING      |
|number	     |STRING      |
|created_date|STRING      |
|filename	 |STRING      |
|load_dt	 |DATE        |

5. Set the following Airflow variables needed for this example:

| Key                   | Value                                           |Example                                   |
| :--------------------- |:---------------------------------------------- |:---------------------------              |
| gcp_project           | *your-gcp-project-id*                           |cloud-comp-df-demo                        |
| gcp_temp_location     | *gcs-bucket-for-dataflow-temp-files*            |gs://my-comp-df-demo-temp/tmp             |
| gcs_completion_bucket | *output-gcs-bucket*                             |my-comp-df-demp-output                    |
| input_field_names     | *comma-separated-field-names-for-delimited-file*|state,gender,year,name,number,created_date|
| bq_output_table       | *bigquery-output-table*                         |my_dataset.usa_names                      |
| email                 | *some-email@mycompany.com*                      |some-email@mycompany.com                  |

 The variables can be set as follows:

 `gcloud composer environments run` **_cloud-composer-env-name_** `variables -- --set` **_key val_**

6. Browse to the Cloud Composer widget in Cloud Console and click on the DAG folder icon as shown below:
![Alt text](img/dag-folder-example.png "Workflow Overview")

7. The DAG folder is essentially a Cloud Storage bucket. Upload the [simple_load_dag.py](simple_load_dag.py) file into the folder:
![Alt text](img/bucket-example.png "DAG Bucket")
8. Upload the Python Dataflow code [process_delimited.py](dataflow/process_delimited.py) into a *dataflow* folder created in the base DAG folder.
9. Finally follow [these](https://cloud.google.com/composer/docs/how-to/using/triggering-with-gcf) instructions to create a Cloud Function.
    - Ensure that the **DAG_NAME** property is set to _**GcsToBigQueryTriggered**_ i.e. The DAG name defined in [simple_load_dag.py](simple_load_dag.py).
    
***

##### Triggering the workflow

The workflow is automatically triggered by Cloud Function that gets invoked when a new file is uploaded into the *input-gcs-bucket*
For this example workflow, the [usa_names.csv](resources/usa_names.csv) file can be uploaded into the  *input-gcs-bucket*

`gsutil cp resources/usa_names.csv gs://` **_input-gcs-bucket_**

***
