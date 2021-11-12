# Machine Learning Classifier using TensorFlow

### Catch up from previous chapters if necessary
If you didn't go through Chapters 2-8, the simplest way to catch up is to copy data from my bucket:
* Go to the 02_ingest folder of the repo, run the program ./ingest_from_crsbucket.sh and specify your bucket name.
* Go to the 04_streaming folder of the repo, run the program ./ingest_from_crsbucket.sh and specify your bucket name.
* Create a dataset named "flights" in BigQuery by typing:
	```
	bq mk flights
	```
* Go to the 05_bqnotebook folder of the repo, run the script to load data into BigQuery:
	```
	bash load_into_bq.sh <BUCKET-NAME>
	```
* In BigQuery, run this query and save the results as a table named trainday
	```
	  #standardsql
	SELECT
	  FL_DATE,
	  IF(MOD(ABS(FARM_FINGERPRINT(CAST(FL_DATE AS STRING))), 100) < 70, 'True', 'False') AS is_train_day
	FROM (
	  SELECT
	    DISTINCT(FL_DATE) AS FL_DATE
	  FROM
	    `flights.tzcorr`)
	ORDER BY
	  FL_DATE
	```
* Go to the 08_dataflow folder of the repo, run the program ./ingest_from_crsbucket.sh and specify your bucket name.


### This Chapter
You can do it two ways: from a notebook or from CloudShell.

#### 1. From AI Platform Notebooks
* Start Cloud AI Platform Notebook instance with TensorFlow 2.1 or greater
* Open a Terminal and type:
  ``` git clone https://github.com/GoogleCloudPlatform/data-science-on-gcp```
* Browse to, and open flights_model_tf2.ipynb
* Run the code to train and deploy the model
* The above code was on a small subset of the model. To run on the full dataset, run the cells in flights_caip.ipynb

#### (Optional) From CloudShell
* Get the model to predict:
    ```
    ./call_predict.py --project=$(gcloud config get-value core/project)
    ```
* Get the model to predict, but also provide a reason:
    ```
    ./call_predict_reason.py --project=$(gcloud config get-value core/project)
    ```
