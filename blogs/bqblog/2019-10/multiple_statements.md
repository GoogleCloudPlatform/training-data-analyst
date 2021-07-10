# Run multiple statements in BigQuery

BigQuery supports running multiple queries in one statement.

```sql
--BigQuery supports multiple statements
--First query to create the table.
CREATE OR REPLACE TABLE business.customer AS 
SELECT  
  123 AS cust_id,   
  'Evan' AS cust_name
; -- Be sure to remember semi-colons!

-- Second query to select results.
SELECT * 
FROM business.customer
WHERE cust_id = 123;
```