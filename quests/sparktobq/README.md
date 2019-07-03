## Migrating from Spark to Dataproc to BigQuery


* [Part 1](01_spark.ipynb): The original Spark code, now running on Dataproc (lift-and-shift).
* [Part 2](02_gcs.ipynb): Replace HDFS by Google Cloud Storage. This enables job-specific-clusters. (cloud-native)
* [Part 3](03_automate.ipynb): Automate everything, so that we can run in a job-specific cluster. (cloud-optimized)
* [Part 4](04_bigquery.ipynb): Load CSV into BigQuery, use BigQuery. (modernize)
* [Part 5](05_functions.ipynb): Using Cloud Functions, launch analysis every time there is a new file in the bucket. (serverless)


## Part 1
* Create a [new Dataproc cluster](https://console.cloud.google.com/dataproc) from the GCP console:
  * Enable access to web interfaces.
  * Expand Advanced Features
  * Specify a staging bucket. Your notebooks will be stored here.
  * Change the Dataproc Image to 1.4 or higher.
  * Turn on the optional opensource components ```Anaconda``` and ```Jupyter``` .
* When cluster is started, click on the JupyterLab Link (in web interfaces menu of new cluster)
  * In a Terminal, ```git clone https://github.com/GoogleCloudPlatform/bigquery-oreilly-book```
  * Type: ```cd bigquery-oreilly-book/05_devel/sparktobq```
  * In an editor, modify ```copy_to_gcs.sh``` to refer to your bucket
  * Type: ```./copy_to_gcs.sh```
  * The notebooks should show up in the menu of JupyterLab
* Open [01_spark.ipynb](01_spark.ipynb), read the cells, and run them.


### Part 2
* From the part 1 notebook (above), replace ```hadoop fs``` by ```gsutil```
* Replace ```hdfs://``` by ```gs://```
* Make sure to store output to Google Cloud Storage
* Run the notebook

### Part 3
* Add ```%%writefile``` to the cells to export out a PySpark file
* Test running it standalone
* You may have to replace uses of ```gsutil``` within Spark code by Python API
* From CloudShell:
  * 
  * Use the script [submit_onejob.sh](submit_onejob.sh) to submit the created file ```spark_analysis.py``` to the cluster you have created above.
  * Wait for job to finish.
  * Delete the ```sparktobq``` cluster -- you don't need it any more.
  * Use the script [submit_workflow.sh](submit_workflow.sh) to submit a workflow template -- this will create a new cluster, run the job, and delete the cluster.


### Part 4
* Start a AI Platform Notebooks instance
* git clone this repository
* Run ```04_bigquery.ipynb```

### Part 5
* 