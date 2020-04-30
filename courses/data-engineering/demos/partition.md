# Create date-partitioned tables

1. Open BigQuery: https://console.cloud.google.com/bigquery
2. Create a dataset titled `ecommerce` 
3. Copy and Paste the below query

## Find all ecommerce transactions in 2018 and beyond
```sql
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
```

We processed data but got no results! 

Let's create a partitioned table so BigQuery can scan our data more efficiently and not process data it doesnt need.

## Create a date-partitioned table with SQL DDL

```sql
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
```

## Retry the previous query

```sql
SELECT
  total_transactions,
  date_formatted
FROM
  `data-to-insights.ecommerce.partitions`
WHERE date_formatted >= '2018-01-01'
ORDER BY date_formatted DESC
# .7 seconds, 0 bytes processed
# it knows there are no 2018 partitions
```

No data processed. Why? 

Because the dataset only goes until 2017! 2018 data (and therefore data partitions) do not exist. 
