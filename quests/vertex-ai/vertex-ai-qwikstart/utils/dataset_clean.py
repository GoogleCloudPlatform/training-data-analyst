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
"""TODO."""

dataset_clean_query = """
CREATE OR REPLACE TABLE `@CLEAN_TABLE_ID` 
AS (
WITH
  customer_daily_sales AS (
      SELECT
        CustomerID AS customer_id,
        Country AS customer_country,
        EXTRACT(DATE FROM InvoiceDate) AS order_date,
        COUNT(DISTINCT InvoiceNo) AS n_purchases,
        SUM(Quantity) AS order_qty,
        ROUND(SUM(UnitPrice * Quantity), 2) AS revenue
      FROM
        `@RAW_TABLE_ID`
      WHERE
        CustomerID IS NOT NULL
        AND Quantity > 0
      GROUP BY
        customer_id,
        customer_country,
        order_date)

SELECT
  customer_id,
  customer_country,
  order_date,
  n_purchases,
  order_qty,
  revenue
FROM 
  customer_daily_sales
)

"""