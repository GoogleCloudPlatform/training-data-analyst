/*

Demo: Create date-partitioned tables

1. Open BigQuery: https://console.cloud.google.com/bigquery

2. Create a dataset titled ecommerce (if not done already)

3. Copy and Paste the below query
*/

SELECT
  COUNT(transactionId) AS total_transactions,
  date
FROM
  `data-to-insights.ecommerce.all_sessions`
WHERE
  transactionId IS NOT NULL
  AND PARSE_DATE("%Y%m%d", date) >= '2018-01-01'
GROUP BY date
ORDER BY date DESC
# This query will process 205.9 MB when run.
# 1.3 seconds, 0 results

/*
4. Let's partition the table by visitor date

*/

CREATE OR REPLACE TABLE ecommerce.partitions
 PARTITION BY date_formatted
 OPTIONS(
   description="a table partitioned by date"
 ) AS


SELECT
  COUNT(transactionId) AS total_transactions,
  PARSE_DATE("%Y%m%d", date) AS date_formatted
FROM
  `data-to-insights.ecommerce.all_sessions`
WHERE
  transactionId IS NOT NULL
GROUP BY date

/*
5. Now let's try the same query but on the new table

*/

SELECT
  total_transactions,
  date_formatted
FROM
  `data-to-insights.ecommerce.partitions`
WHERE date_formatted >= '2018-01-01'
ORDER BY date_formatted DESC
# .7 seconds, 0 bytes processed
# it knows there are no 2018 partitions

/*
6. Let's try a different filter

*/

SELECT
  total_transactions,
  date_formatted
FROM
  `data-to-insights.ecommerce.partitions`
WHERE date_formatted >= '2017-08-01'
ORDER BY date_formatted DESC
# we get the dual benefits of having stored the data in a table
# and also can call upon partitions by date










