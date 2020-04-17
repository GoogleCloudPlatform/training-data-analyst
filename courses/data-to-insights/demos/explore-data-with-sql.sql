# Demo: Exploring Ecommerce Data with SQL

# 1. Open BigQuery: https://console.cloud.google.com/bigquery

# 2. Copy and Paste portions of the script one at a time (or use bulk comments)

# 3. Work through each by executing selected and highlighting key SQL insights


# What is wrong with the below query?
SELECT 
  fullVisitorId,
  country,
  timeOnSite
FROM
all_sessions # <--- what's missing
LIMIT 10


# Be sure to include the dataset name
SELECT 
  fullVisitorId,
  country,
  timeOnSite
FROM
<dataset-name>.all_sessions # <--- at a minimum
LIMIT 10


# Use backticks ` around project names in SQL only if they contain hyphens 
SELECT column
FROM `project-name.dataset.table`


# If you omit project-name, BigQuery will assume the project is your current one
SELECT column
FROM dataset.table


# Read BigQuery error messages for helpful tips
SELECT 
  fullVisitorId,
  country,
  timeOnSite
FROM
all_sessions
LIMIT 10
# Error: Table name "all_sessions" cannot be resolved: dataset name is missing.


# Avoid using SELECT * to explore data. Try the built-in Preview tab in BigQuery
SELECT * # <--- bad practice
FROM
`data-to-insights.ecommerce.all_sessions`

# Recap: Avoid selecting columns and rows you don’t need
SELECT 
  fullVisitorId, # <--- best practice: spell out the columns you want
  country,
  timeOnSite
FROM
`data-to-insights.ecommerce.all_sessions`
LIMIT 10 # <--- if you're exploring, limit the rows returned
# Note: Running the same query again gives you a cached result (if available*)


# *Unless you have non-deterministic elements
SELECT 
  current_timestamp(),
  fullVisitorId,
  country,
  timeOnSite
FROM
`data-to-insights.ecommerce.all_sessions`
LIMIT 10


# Use ORDER BY and LIMIT to get the top 10 visitors who spent time on our website ... 
SELECT 
  fullVisitorId,
  country,
  timeOnSite
FROM
`data-to-insights.ecommerce.all_sessions`
ORDER BY timeOnSite DESC
LIMIT 10
# Returns duplicate records (data is not at visitor-level granularity)


# Deduplicate with DISTINCT
SELECT DISTINCT
  fullVisitorId,
  country,
  timeOnSite
FROM
`data-to-insights.ecommerce.all_sessions`
ORDER BY timeOnSite DESC
LIMIT 10


# Let’s create a calculated fields for session duration in minutes (instead of seconds)
SELECT DISTINCT
  fullVisitorId,
  country,
  timeOnSite / 60 AS session_time_minutes
FROM
`data-to-insights.ecommerce.all_sessions`
ORDER BY session_time_minutes DESC
LIMIT 10


# Let’s use a ROUND function to clean up the results
SELECT DISTINCT
  fullVisitorId,
  country,
  ROUND(timeOnSite / 60,2) AS session_time_minutes
FROM
`data-to-insights.ecommerce.all_sessions`
ORDER BY session_time_minutes DESC
LIMIT 10



# Let’s filter for all sessions greater than 4 hours (240 minutes)
SELECT DISTINCT
  fullVisitorId,
  country,
  ROUND(timeOnSite / 60,2) AS session_time_minutes
FROM
`data-to-insights.ecommerce.all_sessions`
WHERE session_time_minutes > 240 # <--- will return error (alias in WHERE)
ORDER BY session_time_minutes DESC
LIMIT 10

# Recap: In SQL, you cannot use an aliased field in the WHERE clause
# When the table is pulled and filtered initially, SELECT statement is not interpreted
# Behavior is SQL language not BigQuery specific
SELECT DISTINCT
  fullVisitorId,
  country,
  ROUND(timeOnSite / 60,2) AS session_time_minutes
FROM
`data-to-insights.ecommerce.all_sessions`
WHERE ROUND(timeOnSite / 60,2) > 240
ORDER BY session_time_minutes DESC # <-- you can ORDER BY <alias>
LIMIT 10


######################
# Demo using hotkeys
# Be sure data-to-insights project is pinned first
# hold ctrl or command (mac) to highlight table names
# Click on the below highlighted name:
SELECT
# Click on Column names in UI to automatically add into your query:

FROM
`data-to-insights.ecommerce.all_sessions`
######################


# Perform calculations over values with aggregation
SELECT
  COUNT(DISTINCT fullVisitorId) AS unique_users
FROM
`data-to-insights.ecommerce.all_sessions`


# Any non-aggregated fields must be in GROUP BY
SELECT
  COUNT(DISTINCT fullVisitorId) AS unique_users,
  country
FROM
`data-to-insights.ecommerce.all_sessions`
GROUP BY country # <--- all other fields must be here
ORDER BY unique_users DESC
LIMIT 5



# Investigate uniqueness with COUNT(DISTINCT field)
SELECT
  COUNT(DISTINCT fullVisitorId) AS unique_users,
  COUNT(fullVisitorId) AS users
FROM
`data-to-insights.ecommerce.all_sessions`
# Result: Seems we have many duplicate visitors?


# Filter for duplicates with COUNT and HAVING
SELECT
  fullVisitorId,
  COUNT(fullVisitorId) AS records
FROM
`data-to-insights.ecommerce.all_sessions`
GROUP BY fullVisitorId
HAVING records > 1 # <-- filters data after aggregations
LIMIT 10




# Insight: fullVisitorId can be duplicative because
# the data is at the product view level (not rolled up session level)
SELECT
  fullVisitorId,
  date,
  time,
  pageviews,
  pageTitle,
  v2ProductName
FROM
`data-to-insights.ecommerce.all_sessions`
WHERE fullVisitorId = '8919336618754256169'
ORDER BY date, time
LIMIT 100


# Using CAST to convert between data types
SELECT CAST("12345" AS INT64)

SELECT CAST("2017-08-01" AS DATE)

SELECT CAST(1112223333 AS STRING)

SELECT SAFE_CAST("apple" AS INT64)


# Dealing with NULL values
# Filter all records for only those with transaction IDs
SELECT DISTINCT
  fullVisitorId,
  date,
  time,
  pageviews,
  pageTitle,
  v2ProductName,
  transactionId
FROM
`data-to-insights.ecommerce.all_sessions`
WHERE transactionId IS NOT NULL
ORDER BY date, time
LIMIT 100

# Issue: One transaction can have many Products (differing level of data granularity)

# Solution 1: Use a string aggregation function to combine all products ordered:
SELECT
  transactionId,
  (totalTransactionRevenue / 1000000) AS revenue,
  # Aggregate into a single comma separated field:
  STRING_AGG(v2ProductName) AS product_list
FROM
`data-to-insights.ecommerce.all_sessions`
WHERE transactionId IS NOT NULL
GROUP BY transactionId, totalTransactionRevenue
ORDER BY revenue DESC
LIMIT 100

# Solution 2: Use an array aggregation function to combine all products ordered:
SELECT
  transactionId,
  (totalTransactionRevenue / 1000000) AS revenue,
  # Aggregate into elements of an ARRAY:
  ARRAY_AGG(v2ProductName) AS product_list
FROM
`data-to-insights.ecommerce.all_sessions`
WHERE transactionId IS NOT NULL
GROUP BY transactionId, totalTransactionRevenue
ORDER BY revenue DESC
LIMIT 100
# All products are now elements in the product_list array (still just one row!)
# We'll revisit ARRAYS in great detail later...


# Parsing string values with string functions
SELECT CONCAT("12345","678")

SELECT ENDS_WITH("Apple","e")

SELECT LOWER("Apple")

SELECT REGEXP_CONTAINS("Lunchbox",r"^*box$")
# https://cloud.google.com/bigquery/docs/reference/standard-sql/functions-and-operators#regexp_contains


# Wildcard operators
# Finding all products with ‘shirt’ the name:
SELECT DISTINCT
  v2ProductName
FROM
`data-to-insights.ecommerce.all_sessions`
WHERE LOWER(v2ProductName) LIKE '%shirt%'
LIMIT 100


# WITH clauses
# When writing complex queries, consider breaking apart the logic using WITH clauses
WITH product_views AS (
	# all products
	SELECT
	  COUNT(DISTINCT fullVisitorId) AS visitors,
	  v2ProductName
	FROM
	`data-to-insights.ecommerce.all_sessions`
	GROUP BY v2ProductName
)

# popular shirts
SELECT * FROM product_views
WHERE LOWER(v2ProductName) LIKE '%shirt%'
AND visitors > 10000
ORDER BY visitors DESC
# WITH clauses are effectively sub-queries and can be changed together. 
# If you are continually using a certain WITH clause, 
# consider promoting it to a view or table (covered soon)











































