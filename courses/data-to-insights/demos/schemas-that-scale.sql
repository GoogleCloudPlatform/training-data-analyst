/*

Demo: Practicing with ARRAYs and STRUCTs in BigQuery

based off of: https://www.youtube.com/watch?v=0d5hGVQOrQ0&feature=youtu.be&t=2228

1. Open BigQuery: https://console.cloud.google.com/bigquery

2. Create a dataset titled ecommerce (if not done already)

3. Copy and Paste the below queries and use Execute Selected as you work through them

# Part 1: Practice with ARRAY syntax

*/

# an ARRAY is an ordered set of values that share a datatype
SELECT ARRAY<STRING>
['raspberry', 'blackberry', 'strawberry', 'cherry']
AS fruit_array



# BigQuery can infer the type
SELECT ARRAY
['raspberry', 'blackberry', 'strawberry', 'cherry']
AS fruit_array


# How can you access a specific array element?
# Let's try OFFSET(#)
WITH fruits AS (SELECT ['raspberry', 'blackberry', 'strawberry', 'cherry'] AS fruit_array)
SELECT fruit_array[OFFSET(2)] # what is returned?
AS zero_indexed
FROM fruits



# What about with ORDINAL?
WITH fruits AS (SELECT ['raspberry', 'blackberry', 'strawberry', 'cherry'] AS fruit_array)
SELECT fruit_array[ORDINAL(2)] # how about now?
AS one_indexed
FROM fruits


# Can I count all the elements in my array?
# How many items did a customer add to their basket?
WITH fruits AS (SELECT ['raspberry', 'blackberry', 'strawberry', 'cherry'] AS fruit_array)
SELECT ARRAY_LENGTH(fruit_array) # count
AS array_size
FROM fruits



# Review: Different levels of granularity
SELECT
['apple','pear', 'plum'] AS item,
'Jacob' AS customer
# How we can do normal SQL operations on arrays then?

# Now back to our ecommerce schema         
SELECT
 visitId,
 totals.pageviews,
 totals.timeOnsite,
 trafficSource.source,
 device.browser,
 device.isMobile,
 hits.page.pageTitle  # <-- woah, double nested (you can *technically* go up to 15 deep!)
FROM `bigquery-public-data.google_analytics_sample.ga_sessions_20170801`
WHERE totals.timeOnSite IS NOT NULL
LIMIT 10
# Error: Can't access array field


# fixing the query 
SELECT DISTINCT
 visitId,
 totals.pageviews,
 totals.timeOnsite,
 trafficSource.source,
 device.browser,
 device.isMobile,
 h.page.pageTitle
FROM `bigquery-public-data.google_analytics_sample.ga_sessions_20170801`,
UNNEST(hits) AS h # <--- let's break apart the array so we can query it
WHERE totals.timeOnSite IS NOT NULL
ORDER BY visitId
LIMIT 10

