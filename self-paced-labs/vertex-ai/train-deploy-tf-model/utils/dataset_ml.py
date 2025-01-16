# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

dataset_ml_query = """
CREATE OR REPLACE TABLE `@ML_TABLE_ID` 
AS (
WITH
-- Calculate features before CUTOFF_DATE date.
  features AS (
      SELECT
        customer_id,
        customer_country,
        COUNT(n_purchases) AS n_purchases,
        AVG(order_qty) AS avg_purchase_size,
        AVG(revenue) AS avg_purchase_revenue,
        DATE_DIFF(MAX(order_date), MIN(order_date), DAY) AS customer_age,
        DATE_DIFF(DATE('2011-09-01'), MAX(order_date), DAY) AS days_since_last_purchase
      FROM
        `@CLEAN_TABLE_ID`
      WHERE
        order_date <= DATE('2011-09-01')
      GROUP BY
        customer_id,
        customer_country),
  
  -- Calculate customer target monetary value over historical period + 3M future period.
  label AS (
    SELECT
      customer_id,
      SUM(revenue) AS target_monetary_value_3M
    FROM 
      `@CLEAN_TABLE_ID`
    WHERE
      order_date < DATE('2011-12-01')
    GROUP BY
      customer_id
  )

SELECT
  features.customer_id,
  features.customer_country,
  features.n_purchases, -- frequency
  features.avg_purchase_size, --monetary
  features.avg_purchase_revenue, --monetary
  features.customer_age,
  features.days_since_last_purchase, --recency
  label.target_monetary_value_3M, --target
  CASE 
    WHEN MOD(ABS(FARM_FINGERPRINT(CAST(features.customer_id AS STRING))), 10) < 8
      THEN 'TRAIN'
    WHEN MOD(ABS(FARM_FINGERPRINT(CAST(features.customer_id AS STRING))), 10) = 9
      THEN 'VALIDATE'
    ELSE
      'TEST' END AS data_split
FROM 
  features
INNER JOIN label 
  ON features.customer_id = label.customer_id
);
"""