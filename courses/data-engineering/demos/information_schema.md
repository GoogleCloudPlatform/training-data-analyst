# Practice using INFORMATION_SCHEMA and __TABLES__ to explore metadata

## Querying dataset metadata
BigQuery stores metadata about each object stored in it. You can query these metadata tables to get a better understanding of a dataset and it's contents. [See documentation.](https://cloud.google.com/bigquery/docs/dataset-metadata)

## Query 1: How large are the tables within a given dataset?
Choose a public dataset name from the previous query. We will choose `baseball` for this example but feel free to modify (try other datasets like `new_york` or `san_francisco`).

```sql
-- Querying table metadata to get table size
-- Pick any dataset in the bigquery-public-dataset and tell me

-- How many tables it contains?
-- What is the largest table in GB?
-- What is the largest table in row count?

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
```

## Query 2: How many columns of data are present?

```sql
-- For the dataset you chose, how many columns of data are present?

SELECT * FROM 
  -- Replace baseball with a different dataset:
 `bigquery-public-data.baseball.INFORMATION_SCHEMA.COLUMNS`;
```

## Query 3: Are any columns partitioned or clustered columns?

```sql
-- Are there any partitioned or clustered columns?

SELECT * FROM 
  -- Replace baseball with a different dataset:
 `bigquery-public-data.baseball.INFORMATION_SCHEMA.COLUMNS`
WHERE 
  is_partitioning_column = 'YES' OR clustering_ordinal_position IS NOT NULL;
```

## Query 4: Querying metadata across datasets

```sql
-- Question: If you wanted to query across multiple datasets, how could you do it?
-- https://stackoverflow.com/questions/43457651/bigquery-select-tables-from-all-tables-within-project
-- Answer: With a UNION or a python script to iterate through each dataset in `bq ls`

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
```

Which table had the most rows in the previous example?

## Optional: Query 5: Viewing all datasets within a GCP project

If you already have BigQuery datasets and tables stored on your project, you can quickly view metadata for all your datasets using `INFORMATION_SCHEMA`. The below query shows just a simple example of viewing when each dataset in your project was created. 

```sql
SELECT
 s.*,
 TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), creation_time, DAY) AS days_live,
 option_value AS dataset_description
FROM
 `<your-project-name>.INFORMATION_SCHEMA.SCHEMATA` AS s
 LEFT JOIN `<your-project-name>.INFORMATION_SCHEMA.SCHEMATA_OPTIONS` AS so
 USING (schema_name)

WHERE so.option_name = 'description'
 
ORDER BY last_modified_time DESC

LIMIT 15;
```

Note: You will need to replace <your-project-name> with a BigQuery project you can query against that has existing datasets. 
 
Final Note: You can use the data from `INFORMATION_SCHEMA` to creatively 're-create' your entire dataset with SQL DDL. See the below example link: https://cloud.google.com/bigquery/docs/information-schema-tables#advanced_example
