/*

Demo: Query 10 billion rows of Wikipedia data in BigQuery

1. Open BigQuery: https://console.cloud.google.com/bigquery

2. Copy and Paste the below query
*/

SELECT
  language,
  title,
  SUM(views) AS views
FROM
  `bigquery-samples.wikipedia_benchmark.Wiki10B`
WHERE
  title LIKE '%Google%'
GROUP BY
  language,
  title
ORDER BY
  views DESC;

/*
Google BigQuery has numerous Public Datasets that anyone can query. One of these is all public wikipedia page metadata. 
Let’s run a SQL query to see how fast we can scan and process 10 Billion rows looking for the word “Google” in the Wikipedia Page Title. 

3. Point out the amount of data the query will process by clicking on the validator (around 500 GB)

4. Run the Query 

5. Point out the processing time (should be around 12 seconds)

6. Point out the results of the Query showing the main “Google” wikipedia page has been viewed over 9 Billion times

7. Lastly, click on the query Explanation button to show how many input and output rows. 

Poll the class: What do the 10 Billion input rows signify? What about the resulting 200K+ output? The 10 Billion rows correspond to the count of Wikipedia pages and the 200K+ final result is the count of pages that contained the word “Google” somewhere in the title. 

Poll the class: Do you think the query will run faster, slower, or depends on the resources if we re-ran it right now?


8. Re-Run the Query (cache enabled)

The same query executed much faster as it is now pulling from query cache. We’ll discuss this more in the Performance section of the course. 

Last Poll: Do you think it matters that we spelled Google with a capital “G” when matching against title? Is SQL case sensitive? In the LIKE operator, yes! 

9. Re-Run the Query changing ‘%Google%’ to ‘%google%’ in the LIKE operator

The results are wildly different now. We will review pitfalls like these in our SQL exercises as part of this course. It is your responsibility as a data analyst to understand what your query is actually doing. 
*/


/*
# Demo option #2:
# Taxi Trips in Chicago

# Finds taxifare by hour for picks that happen in downtown Chicago. Using pickup_community_area = 76 will give you O'Hare

SELECT
hour,
AVG(fare) AS avg_fare
FROM (
	SELECT
	EXTRACT(HOUR
	FROM
	trip_start_timestamp) AS hour,
	fare
	FROM
	`bigquery-public-data.chicago_taxi_trips.taxi_trips` 
	WHERE pickup_community_area = 32
)
GROUP BY hour
ORDER BY avg_fare DESC
*/
