# 5. Interactive data exploration

### Catch up from previous chapters if necessary
If you didn't go through Chapters 2-4, the simplest way to catch up is to copy data from my bucket:
* Go to the 02_ingest folder of the repo, run the program ./ingest_from_crsbucket.sh and specify your bucket name.
* Go to the 04_streaming folder of the repo, run the program ./ingest_from_crsbucket.sh and specify your bucket name.
* Create a dataset named "flights" in BigQuery by typing:
	```
	bq mk flights
	```


### Load the CSV files created in Chapter 3 into BigQuery
* Open CloudShell and navigate to 05_bqnotebook
* Run the script to load data into BigQuery:
	```
	bash load_into_bq.sh <BUCKET-NAME>
	```
* Visit the BigQuery console to query the new table:
	```
	SELECT
	  *
	FROM (
	  SELECT
	    ORIGIN,
	    AVG(DEP_DELAY) AS dep_delay,
	    AVG(ARR_DELAY) AS arr_delay,
	    COUNT(ARR_DELAY) AS num_flights
	  FROM
	    flights.tzcorr
	  GROUP BY
	    ORIGIN )
	WHERE
	  num_flights > 3650
	ORDER BY
	  dep_delay DESC
	
	``` 
* In BigQuery, run this query to save the results as a table named trainday
	```
	CREATE OR REPLACE TABLE flights.trainday AS
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
  This table will be used throughout the rest of the book.

* Start up a Cloud AI Platforms Notebook instance.

* Start a new notebook. Then, copy and paste cells from <a href="exploration.ipynb">exploration.ipynb</a> and click Run to execute the code.


