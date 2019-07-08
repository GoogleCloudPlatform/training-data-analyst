-- This example script shows how to create a table with
-- descriptions and labels to help downstream users know what's in it
--
-- Documentation: https://cloud.google.com/bigquery/docs/reference/standard-sql/data-definition-language#create_table_statement
CREATE OR REPLACE TABLE
coursera_analytics.table_name
(
  ldap string OPTIONS(description = 'The LDAP of the employee'),
  team string OPTIONS(
    description = 'What team the person belongs to TCD: Technical Curriculum Developer'
    )
)
OPTIONS(
    description = 'Your detailed and lengthly table description goes here.',
    labels=[("team", "tcd")] -- Must be lowercase.

)
AS
-- Create a table from this query:
SELECT
  -- Note: Column aliases here will be overwritten by the above schema definition
  -- if conflicts exist
  'evanjones' AS ldap,
  'TCD' AS team
