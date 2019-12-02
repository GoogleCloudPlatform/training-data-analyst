# Create a simple upstream health check 

BigQuery supports running multiple statements in one query and they are executed in series (top to bottom). You can take advantage of this serial execution to force one of the queries to error if a certain health check is not met. We will use the standard SQL `ERROR` function and a simple `IF` condition to check if an upstream data source has any rows.

## Create a sample data table

```sql
--Be sure to create a dataset called "business" before running the below

-- Create a customer table
CREATE OR REPLACE TABLE business.customer AS

SELECT  
  123 AS cust_id,
  'Evan' AS name;

SELECT * FROM business.customer;
```

## Simulate bad data by deleting all the records

```sql
-- Remove all rows from upstream table to simulate bad upstream source
DELETE FROM business.customer WHERE true;
```

## Add a health check to your queries to mandate upstream data is present
```sql
-- First query to check health of upstream table
-- Assume row_count must be greater than zero or return error.
SELECT 
  COUNT(*) AS row_count
FROM business.customer
HAVING
  IF(row_count > 0, true,
    ERROR(
      FORMAT('Error: row_count must be positive but is %t',row_count)
      )
    );

-- Run this second query for our dashboard ONLY IF the previous health check passed
SELECT * FROM business.customer
WHERE cust_id = 123;
```
