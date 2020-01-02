/*

Demo: Joining weather datasets

1. Open BigQuery: https://console.cloud.google.com/bigquery

2. Create a dataset titled ecommerce (if not done already)

3. Copy and Paste the below query
*/

SELECT
  # temperature sensor data
  a.stn,
  a.wban,
  a.temp,
  a.year,
  
  # weather station info
  b.name,
  b.state,
  b.country
  
# pull sensor data from GSOD daily temp tables
FROM `bigquery-public-data.noaa_gsod.gsod*` AS a

# JOIN against station lookup table (has full name & state info)
JOIN `bigquery-public-data.noaa_gsod.stations` AS b # default is INNER JOIN
ON
  # NOAA data requires a JOIN on these two keys:
  a.stn=b.usaf AND a.wban=b.wban
  
WHERE
  # Filter data
  state IS NOT NULL
  AND country='US'
  
  # filer table suffix wildcards:
  AND _TABLE_SUFFIX = '2018' # filter for just 2018

/*
3. How many rows were returned? 
Answer: 893,668

4. Let's add a new weather station that was just installed at Google's campus 
It was just added to the noaa_gsod.stations table but may not have temperature readings yet
*/

WITH add_weather_station AS (
SELECT usaf, wban, name, state, country FROM `bigquery-public-data.noaa_gsod.stations` 
  UNION ALL
  SELECT 'GOOG' AS usaf, 'GOOG123' AS wban, 'New Google HQ Sensor' AS name, 'CA' AS state, 'US' AS country
)

SELECT * FROM add_weather_station
WHERE name = 'New Google HQ Sensor'

/*

5. Now let's JOIN against weather station readings and filter for our new Google weather station

*/

SELECT
  # temperature sensor data
  a.stn,
  a.wban,
  a.temp,
  a.year,
  
  # weather station info
  b.name,
  b.state,
  b.country
  
# pull sensor data from GSOD daily temp tables
FROM `bigquery-public-data.noaa_gsod.gsod*` AS a

# JOIN against station lookup table (has full name & state info)
JOIN # default is INNER JOIN

(SELECT usaf, wban, name, state, country FROM `bigquery-public-data.noaa_gsod.stations` 
  UNION ALL
  SELECT 'GOOG' AS usaf, 'GOOG123' AS wban, 'New Google HQ Sensor' AS name, 'CA' AS state, 'US' AS country
)AS b 
ON
  # NOAA data requires a JOIN on these two keys:
  a.stn=b.usaf AND a.wban=b.wban
  
WHERE
  # Filter data
  state IS NOT NULL
  AND country='US'
  
  AND name = 'New Google HQ Sensor'
  
/*

5. Why don't we get any results? Let's try a LEFT JOIN instead

*/

SELECT
  # temperature sensor data
  a.stn,
  a.wban,
  a.temp,
  a.year,
  
  # weather station info
  b.name,
  b.state,
  b.country
  
# pull sensor data from GSOD daily temp tables
FROM `bigquery-public-data.noaa_gsod.gsod*` AS a

# JOIN against station lookup table (has full name & state info)
LEFT JOIN

(SELECT usaf, wban, name, state, country FROM `bigquery-public-data.noaa_gsod.stations` 
  UNION ALL
  SELECT 'GOOG' AS usaf, 'GOOG123' AS wban, 'New Google HQ Sensor' AS name, 'CA' AS state, 'US' AS country
)AS b 
ON
  # NOAA data requires a JOIN on these two keys:
  a.stn=b.usaf AND a.wban=b.wban
  
WHERE
  # Filter data
  state IS NOT NULL
  AND country='US'
  
  AND name = 'New Google HQ Sensor'
  
/*

6. HMMM... what about a RIGHT JOIN?

*/

SELECT
  # temperature sensor data
  a.stn,
  a.wban,
  a.temp,
  a.year,
  
  # weather station info
  b.name,
  b.state,
  b.country
  
# pull sensor data from GSOD daily temp tables
FROM `bigquery-public-data.noaa_gsod.gsod*` AS a

# JOIN against station lookup table (has full name & state info)
RIGHT JOIN

(SELECT usaf, wban, name, state, country FROM `bigquery-public-data.noaa_gsod.stations` 
  UNION ALL
  SELECT 'GOOG' AS usaf, 'GOOG123' AS wban, 'New Google HQ Sensor' AS name, 'CA' AS state, 'US' AS country
)AS b 
ON
  # NOAA data requires a JOIN on these two keys:
  a.stn=b.usaf AND a.wban=b.wban
  
WHERE
  # Filter data
  state IS NOT NULL
  AND country='US'
  
  AND name = 'New Google HQ Sensor'
  
/*

7. There it is!! But what are all those NULL values? And why did a RIGHT JOIN work in this case?

Discussion: venn diagrams of JOINs and what records get returned when

*/