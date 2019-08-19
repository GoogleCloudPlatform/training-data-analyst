/*

Demo: Creating an authorized View in BigQuery

based off of: https://cloud.google.com/bigquery/docs/share-access-views

1. Open BigQuery: https://console.cloud.google.com/bigquery

2. Create a dataset titled ecommerce (if not done already)

Scenario: Your anti-fraud team has asked you to create a report that lists the 10 most recent transactions that have an order amount of 1,000 or more for them to review manually.

Task: Create a new view that returns all the most recent 10 transactions with revenue greater than 1,000 on or after January 1st, 2017.

3. Copy and Paste the below query

*/

CREATE OR REPLACE VIEW ecommerce.vw_large_transactions
OPTIONS(
  description="large transactions for review",
  labels=[('org_unit','loss_prevention')]
)
AS
SELECT DISTINCT
  date,
  fullVisitorId,
  visitId,
  channelGrouping,
  totalTransactionRevenue / 1000000 AS totalTransactionRevenue,
  currencyCode,
  STRING_AGG(DISTINCT v2ProductName ORDER BY v2ProductName LIMIT 10) AS products_ordered
 FROM `data-to-insights.ecommerce.all_sessions_raw`
 WHERE
  (totalTransactionRevenue / 1000000) > 1000
  AND currencyCode = 'USD'

 GROUP BY 1,2,3,4,5,6
  ORDER BY date DESC # latest transactions

  LIMIT 10
;

/*
__Scenario:__ Your data team lead has asked you to come up with a way to limit who in your organization can see the data returned by the view you just created. Order information is especially sensitive and needs to be shared only with users that have a need to see such information.

__Task:__ Modify the view you created earlier to only allow logged in users with a qwiklabs.net session domain to be able to see the data in the underlying view. (Note: You will be creating specific user group whitelists in a later lab on access; for now you are validating based on the session user's domain).

To view your own session login information, run the below query that uses SESSION_USER():

*/
SELECT
  SESSION_USER() AS viewer_ldap;

/*

Take note of the domain returned by the above query

The below query only shows rows to @qwiklabs.net users:

*/
SELECT DISTINCT
  SESSION_USER() AS viewer_ldap,
  REGEXP_EXTRACT(SESSION_USER(), r'@(.+)') AS domain,
  date,
  fullVisitorId,
  visitId,
  channelGrouping,
  totalTransactionRevenue / 1000000 AS totalTransactionRevenue,
  currencyCode,
  STRING_AGG(DISTINCT v2ProductName ORDER BY v2ProductName LIMIT 10) AS products_ordered
 FROM `data-to-insights.ecommerce.all_sessions_raw`
 WHERE
  (totalTransactionRevenue / 1000000) > 1000
  AND currencyCode = 'USD'
  AND REGEXP_EXTRACT(SESSION_USER(), r'@(.+)') IN ('qwiklabs.net') # <--- adjust domain as needed

 GROUP BY 1,2,3,4,5,6,7,8
  ORDER BY date DESC # latest transactions

  LIMIT 10

/*

Adjust the domain filter in the IN clause to test what rows get returned

Finally, let's create a view on top of the query we created earlier. 
We'll also add optional parameters like auto-expiration after 90 days and 
label the view for the loss_prevention unit to find:

*/



CREATE OR REPLACE VIEW ecommerce.vw_large_transactions
OPTIONS(
  description="large transactions for review",
  labels=[('org_unit','loss_prevention')],
  expiration_timestamp=TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)
)
AS
#standardSQL
SELECT DISTINCT
  SESSION_USER() AS viewer_ldap,
  REGEXP_EXTRACT(SESSION_USER(), r'@(.+)') AS domain,
  date,
  fullVisitorId,
  visitId,
  channelGrouping,
  totalTransactionRevenue / 1000000 AS totalTransactionRevenue,
  currencyCode,
  STRING_AGG(DISTINCT v2ProductName ORDER BY v2ProductName LIMIT 10) AS products_ordered
 FROM `data-to-insights.ecommerce.all_sessions_raw`
 WHERE
  (totalTransactionRevenue / 1000000) > 1000
  AND currencyCode = 'USD'
  AND REGEXP_EXTRACT(SESSION_USER(), r'@(.+)') IN ('qwiklabs.net')

 GROUP BY 1,2,3,4,5,6,7,8
  ORDER BY date DESC # latest transactions

  LIMIT 10;

/*

Note: If you didn't want to filter on domain, you could always have a lookup table
of email address or usernames and the groups that they belong to. Then you would 
simply JOIN on that table and filter. 

*/


