-- Practice using INFORMATION_SCHEMA and __TABLES__ to explore metadata

-- Querying dataset metadata
-- https://cloud.google.com/bigquery/docs/dataset-metadata


-- QUERY 1
-- Query table metadata to get table size
-- Pick any dataset in the bigquery-public-dataset and tell me:

-- How many tables it contains?
-- What is the largest table in terms of GB?

-- Dataset options include: bitcoin_blockchain, github_repos, nasa_wildfire, wikipedia, and more

SELECT 
  dataset_id,
  table_id,
  -- Convert bytes to GB.
  ROUND(size_bytes/pow(10,9),2) as size_gb,
  -- Convert UNIX EPOCH to a timestamp.
  TIMESTAMP_MILLIS(creation_time) AS creation_time,
  TIMESTAMP_MILLIS(last_modified_time) as last_modified_time,
  row_count,
  CASE 
    WHEN type = 1 THEN 'table'
    WHEN type = 2 THEN 'view'
  ELSE NULL
  END AS type
FROM
  -- Replace baseball with a different dataset:
  `bigquery-public-data.baseball.__TABLES__`
ORDER BY size_gb DESC;

-- Modify the query above to determine the largest table in terms of row count
-- Is the same table as the largest in terms of GB?


-- QUERY 2
-- For the dataset you chose, how many columns of data are present?

SELECT * FROM 
  -- Replace baseball with a different dataset:
 `bigquery-public-data.baseball.INFORMATION_SCHEMA.COLUMNS`;


-- QUERY 3
-- Are there any partitioned or clustered columns?
-- For some datasets, this query will return no results. 
-- Running this query on the wikipedia dataset will return results.

SELECT * FROM 
  -- Replace baseball with a different dataset:
 `bigquery-public-data.baseball.INFORMATION_SCHEMA.COLUMNS`
WHERE 
  is_partitioning_column = 'YES' OR clustering_ordinal_position IS NOT NULL;


-- QUERY 4
-- Question: If you wanted to query across multiple datasets, how could you do it?
-- https://stackoverflow.com/questions/43457651/bigquery-select-tables-from-all-tables-within-project
-- Answer: With a UNION or a Python script to iterate through each dataset in `bq ls`

-- For example, which table has the most rows?

WITH ALL__TABLES__ AS (
  SELECT * FROM `bigquery-public-data.baseball.__TABLES__` UNION ALL
  SELECT * FROM `bigquery-public-data.bls.__TABLES__` UNION ALL
  SELECT * FROM `bigquery-public-data.census_bureau_usa.__TABLES__` UNION ALL
  SELECT * FROM `bigquery-public-data.cloud_storage_geo_index.__TABLES__` UNION ALL
  SELECT * FROM `bigquery-public-data.cms_codes.__TABLES__` UNION ALL
  SELECT * FROM `bigquery-public-data.fec.__TABLES__` UNION ALL
  SELECT * FROM `bigquery-public-data.genomics_cannabis.__TABLES__` UNION ALL
  SELECT * FROM `bigquery-public-data.ghcn_d.__TABLES__` UNION ALL
  SELECT * FROM `bigquery-public-data.ghcn_m.__TABLES__` UNION ALL
  SELECT * FROM `bigquery-public-data.github_repos.__TABLES__` UNION ALL
  SELECT * FROM `bigquery-public-data.hacker_news.__TABLES__` UNION ALL
  SELECT * FROM `bigquery-public-data.irs_990.__TABLES__` UNION ALL
  SELECT * FROM `bigquery-public-data.medicare.__TABLES__` UNION ALL
  SELECT * FROM `bigquery-public-data.new_york.__TABLES__` UNION ALL
  SELECT * FROM `bigquery-public-data.nlm_rxnorm.__TABLES__` UNION ALL
  SELECT * FROM `bigquery-public-data.noaa_gsod.__TABLES__` UNION ALL
  SELECT * FROM `bigquery-public-data.open_images.__TABLES__` UNION ALL
  SELECT * FROM `bigquery-public-data.samples.__TABLES__` UNION ALL
  SELECT * FROM `bigquery-public-data.san_francisco.__TABLES__` UNION ALL
  SELECT * FROM `bigquery-public-data.stackoverflow.__TABLES__` UNION ALL
  SELECT * FROM `bigquery-public-data.usa_names.__TABLES__` UNION ALL
  SELECT * FROM `bigquery-public-data.utility_us.__TABLES__` 
)
SELECT *
FROM ALL__TABLES__
ORDER BY row_count DESC -- Top 10 tables with the most rows
LIMIT 10;



-- EXAMPLE QUERY FOR YOUR OWN PROJECT
-- Note that this query will not run on the BigQuery Public Data project.
-- You can run this query in your own project (e.g. qwiklabs-gcp-XX-XXXXXXXXXX).
-- Identify the most recently modified datasets in project and how long they have been around:

SELECT
 s.*,
 TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), creation_time, DAY) AS days_live,
 option_value AS dataset_description
FROM
  -- Replace project-name with your project name
 `project-name.INFORMATION_SCHEMA.SCHEMATA` AS s
   -- Replace project-name with your project name
 LEFT JOIN `project-name.INFORMATION_SCHEMA.SCHEMATA_OPTIONS` AS so
 USING (schema_name)
 
ORDER BY last_modified_time DESC

LIMIT 15;


-- For advanced examples, see: Using Dataset and Table metadata to create SQL DDL for version control
-- https://cloud.google.com/bigquery/docs/information-schema-tables#advanced_example
