-- Demo from: https://medium.com/google-cloud/bigquery-optimized-cluster-your-tables-65e2f684594b

-- Practice with clustering

-- How much data does this query process?

SELECT 
  wiki,
  SUM(views) AS views
FROM `fh-bigquery.wikipedia_v2.pageviews_2017` 
WHERE DATE(datehour) >= "2017-01-01" 
AND wiki IN ('en', 'en.m')
AND title = 'Kubernetes'
GROUP BY wiki ORDER BY wiki;
-- 43s, 2.2TB processed


-- How much data does this query process?

SELECT 
  wiki,
  SUM(views) AS views
FROM `fh-bigquery.wikipedia_v3.pageviews_2017` 
WHERE DATE(datehour) >= "2017-01-01" 
AND wiki IN ('en', 'en.m')
AND title = 'Kubernetes'
GROUP BY wiki ORDER BY wiki;
-- 43s, 227 GB processed


-- The magic of clustering
-- Here's how the v3 table was created
/*
CREATE TABLE `fh-bigquery.wikipedia_v3.pageviews_2017`
PARTITION BY DATE(datehour)
CLUSTER BY wiki, title
OPTIONS(
   description="Wikipedia pageviews - partitioned by day, clustered by (wiki, title). Contact https://twitter.com/felipehoffa"
   , require_partition_filter=true
)
AS SELECT * FROM `fh-bigquery.wikipedia_v2.pageviews_2017`
WHERE datehour > '1990-01-01' # nag
-- 4724.8s elapsed, 2.20 TB processed
*/
-- Note the order of the clusters matters


-- Unclustered vs clustered
SELECT * 
FROM `fh-bigquery.wikipedia_v2.pageviews_2017` -- Unclustered
WHERE DATE(datehour) BETWEEN '2017-06-01' AND '2017-06-30'
LIMIT 1;
-- 1.8s, 180 GB


SELECT * 
FROM `fh-bigquery.wikipedia_v3.pageviews_2017` -- Clustered
WHERE DATE(datehour) BETWEEN '2017-06-01' AND '2017-06-30'
LIMIT 1;
-- 1.8s, 241 MB (not GB)


-- Unclustered vs clustered
SELECT wiki, SUM(views) views
FROM `fh-bigquery.wikipedia_v2.pageviews_2017` 
WHERE DATE(datehour) BETWEEN '2017-06-01' AND '2017-06-30'
AND wiki LIKE 'en'
AND title = 'Barcelona'
GROUP BY wiki ORDER BY wiki;
-- 18.1s elapsed, 180 GB processed


SELECT wiki, SUM(views) views
FROM `fh-bigquery.wikipedia_v3.pageviews_2017` 
WHERE DATE(datehour) BETWEEN '2017-06-01' AND '2017-06-30'
AND wiki LIKE 'en'
AND title = 'Barcelona'
GROUP BY wiki ORDER BY wiki;
-- 3.5s elapsed, 10.3 GB processed










