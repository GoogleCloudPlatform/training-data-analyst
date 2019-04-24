/*

Demo: Setup a reporting table for the top 5 viewed products -- refreshed daily

1. Open BigQuery: https://console.cloud.google.com/bigquery

2. Create a dataset titled ecommerce (if not done already)

3. Copy and Paste the below query
*/

# recurring query for top 10 products
SELECT
  COUNT(DISTINCT fullVisitorId) AS visitors,
  v2ProductName
FROM
`data-to-insights.ecommerce.all_sessions`
GROUP BY v2ProductName
ORDER BY visitors DESC
LIMIT 10

/*

4. Run the query and note the execution time and bytes processed
# normally about 1.1 GB and 7 seconds

Let's store the top 5 products in a table for faster retrieval

5. In the UI select Schedule Query > Create new Scheduled Query

6. Name the scheduled query: top_products

7. Destination table write preference: OVERWRITE

8. Specify a table name: top_products

9. Click Schedule 

10. In the BigQuery navigation panel select Scheduled queries

11. Locate top_products and click Edit (to make any optional edits like LIMIT 10 --> LIMIT 20)