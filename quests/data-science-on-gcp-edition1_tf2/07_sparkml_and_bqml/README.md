# 7. Machine Learning: Logistic regression on Spark

### Catch up from previous chapters if necessary
If you didn't go through Chapters 2-6, the simplest way to catch up is to copy data from my bucket:

#### Catch up from Chapters 2-4
* Go to the 02_ingest folder of the repo, run the program ./ingest_from_crsbucket.sh and specify your bucket name.
* Go to the 04_streaming folder of the repo, run the program ./ingest_from_crsbucket.sh and specify your bucket name.
* Create a dataset named "flights" in BigQuery by typing:
	```
	bq mk flights
	```
* Go to the 05_bqdatalab folder of the repo, run the script to load data into BigQuery:
	```
	bash load_into_bq.sh <BUCKET-NAME>
	```
 
#### Catch up from Chapter 5
* In BigQuery, run this query and save the results as a table named trainday
	```
	  #standardsql
	SELECT
	  FL_DATE,
	  IF(ABS(MOD(FARM_FINGERPRINT(CAST(FL_DATE AS STRING)), 100)) < 70, 'True', 'False') AS is_train_day
	FROM (
	  SELECT
	    DISTINCT(FL_DATE) AS FL_DATE
	  FROM
	    `flights.tzcorr`)
	ORDER BY
	  FL_DATE
	```

* Export the table as gs://BUCKET/flights/trainday.csv

#### [Optional] Catch up from Chapter 6
* Use the instructions in the <a href="../06_dataproc/README.md">Chapter 6 README</a> to:
  * launch a minimal Cloud Dataproc cluster with initialization actions for Jupyter (`./create_cluster.sh BUCKET ZONE`)

* Start a new notebook and in a cell, download a read-only clone of this repository:
    ```
    %bash
    git clone https://github.com/GoogleCloudPlatform/data-science-on-gcp
    rm -rf data-science-on-gcp/.git
    ```
* Browse to data-science-on-gcp/07_sparkml_and_bqml/logistic_regression.ipynb
  and run the cells in the notebook (change the BUCKET appropriately).

## This Chapter
### Logistic regression using Spark
* If you haven't already done so, launch a minimal Dataproc cluster:
    ```
    cd ~/data-science-on-gcp/06_dataproc
    ./create_cluster.sh BUCKET ZONE
    ```
* Submit a Spark job to run the full dataset (change the BUCKET appropriately).
    ```
    cd ~/data-science-on-gcp/07_sparkml_and_bqml
    ../06_dataproc/increase_cluster.sh
    ./submit_spark.sh BUCKET logistic.py
    ```

### Feature engineering
* Submit a Spark job to do experimentation: `./submit_spark.sh BUCKET experiment.py`

### Cleanup
* Delete the cluster either from the GCP web console or by typing in CloudShell, `../06_dataproc/delete_cluster.sh`

### BigQuery ML
* Start an Cloud AI Platform Notebooks instance (minimal reqs are fine)
* Start a new notebook and in a cell, download a read-only clone of this repository:
    ```
    %bash
    git clone https://github.com/GoogleCloudPlatform/data-science-on-gcp
    rm -rf data-science-on-gcp/.git
    ```
* Browse to data-science-on-gcp/07_sparkml_and_bqml/flights_bqml.ipynb
  and run the cells in the notebook

