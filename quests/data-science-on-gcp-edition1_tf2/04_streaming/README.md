# 4. Streaming data: publication and ingest

### Ingest data if necessary
If you didn't go through Chapter 2, the simplest way to get the files you need is to copy it from my bucket:
* Go to the 02_ingest folder of the repo
* Run the program ./ingest_from_crsbucket.sh and specify your bucket name.


### Batch processing in DataFlow
* Setup:
    ```
	cd simulate; ./install_packages.sh
    ```
* Parsing airports data:
	```
	cd simulate
	./df01.py
	head extracted_airports-00000*
	rm extracted_airports-*
	```
* Adding timezone information:
	```
	./df02.py
	head airports_with_tz-00000*
	rm airports_with_tz-*
	```
* Converting times to UTC:
	```
	./df03.py
	head -3 all_flights-00000*
	```
* Correcting dates:
	```
	./df04.py
	head -3 all_flights-00000*
	rm all_flights-*
	```
* Create events:
	```
	./df05.py
	head -3 all_events-00000*
	rm all_events-*
	```  
### Pipeline on GCP:
* Go to the GCP web console, API & Services section and enable the Dataflow API.
* In CloudShell, type:
	```
	bq mk flights
	gsutil cp airports.csv.gz gs://<BUCKET-NAME>/flights/airports/airports.csv.gz
	./df06.py -p $DEVSHELL_PROJECT_ID -b <BUCKETNAME> --region us-central1
	``` 
* Go to the GCP web console and wait for the Dataflow ch04timecorr job to finish. It might take several  
* Then, navigate to the BigQuery console and type in:
	```
			SELECT
			  ORIGIN,
			  DEP_TIME,
			  DEP_DELAY,
			  DEST,
			  ARR_TIME,
			  ARR_DELAY,
			  NOTIFY_TIME
			FROM
			  flights.simevents
			WHERE
			  (DEP_DELAY > 15 and ORIGIN = 'SEA') or
			  (ARR_DELAY > 15 and DEST = 'SEA')
			ORDER BY NOTIFY_TIME ASC
			LIMIT
			  10
	```
### Stream processing
* In CloudShell, run
	```
    cd simulate
	python3 ./simulate.py --startTime '2015-05-01 00:00:00 UTC' --endTime '2015-05-04 00:00:00 UTC' --speedFactor=30 --project $DEVSHELL_PROJECT_ID
    ```
* In another CloudShell tab, run:
	```
	cd realtime
	./run_oncloud.sh <BUCKET-NAME>
	```
* Go to the GCP web console in the Dataflow section and monitor the job.
* Once you see events being written into BigQuery, you can query them from the BigQuery console:
			```
			#standardsql
			SELECT
			  *
			FROM
			  `flights.streaming_delays`
			WHERE
			  airport = 'DEN'
			ORDER BY
			  timestamp DESC
			```
* In BigQuery, run this query and save this as a view:
	```
		#standardSQL
		SELECT
		  airport,
		  last[safe_OFFSET(0)].*,
		  CONCAT(CAST(last[safe_OFFSET(0)].latitude AS STRING), ",", CAST(last[safe_OFFSET(0)].longitude AS STRING)) AS location
		FROM (
		  SELECT
		    airport,
		    ARRAY_AGG(STRUCT(arr_delay,
		        dep_delay,
		        timestamp,
		        latitude,
		        longitude,
		        num_flights)
		    ORDER BY
		      timestamp DESC
		    LIMIT
		      1) last
		  FROM
		    `flights.streaming_delays`
		  GROUP BY
		    airport )
	```   
* Follow the steps in the chapter to connect to Data Studio and create a GeoMap.
* Stop the simulation program in CloudShell.
* From the GCP web console, stop the Dataflow streaming pipeline.
	
