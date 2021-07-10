# Predict NYC taxi fares using BQML

In this demo, we'll build a model to predict taxifares in NYC using one of BigQuery's public datasets. Note to instructors: you may want to run the CREATE MODEL query before class as it will take up to 10 minutes. Also, BQML DNN regression used here is currently in alpha but should be whitelisted in your Qwiklabs environment.

We'll begin by creating a sampled version of the dataset with a few extra columns we
may need. Sampling will save time during our initial training as well as save cost because BQML model training, like queries, is priced based on the amount of data ingested.

First, create a new dataset named "taxi". Then run the following query to sample about 300,000 rows of the full 1 billion row dataset. The query should take <20s. The query applies some simple quality control in the WHERE clause and creates a dataset identifer of 0, 1, or 2 so we can easily select different rows for training and evaluation.

```sql
#standardSQL
create or replace table `taxi.taxi300k` as
WITH taxi_preproc AS (
SELECT 
  ABS(MOD(FARM_FINGERPRINT(STRING(pickup_datetime)), 10000)) AS dataset,
  (tolls_amount + fare_amount) AS fare_amount,
  pickup_datetime,
  EXTRACT(DAYOFWEEK FROM pickup_datetime) AS dayofweek,
  EXTRACT(HOUR FROM pickup_datetime) AS hourofday,
  pickup_longitude AS pickuplon,
  pickup_latitude AS pickuplat,
  dropoff_longitude AS dropofflon,
  dropoff_latitude AS dropofflat,
  passenger_count
FROM
  `nyc-tlc.yellow.trips` 
WHERE
  trip_distance > 0
  AND fare_amount >= 2.5
  AND fare_amount < 200
  AND pickup_longitude > -78
  AND pickup_longitude < -70
  AND dropoff_longitude > -78
  AND dropoff_longitude < -70
  AND pickup_latitude > 37
  AND pickup_latitude < 45
  AND dropoff_latitude > 37
  AND dropoff_latitude < 45
  AND passenger_count > 0
  AND ABS(MOD(FARM_FINGERPRINT(STRING(pickup_datetime)), 10000)) < 3
  )
  SELECT 
  dataset, 
  fare_amount,
  pickup_datetime,
  hourofday, 
  dayofweek,
  CAST(dayofweek * 24 + hourofday AS STRING) AS dayhour,
  pickuplon,
  pickuplat,
  dropofflon,
  dropofflat,
  SQRT(POW((pickuplon - dropofflon),2) + POW(( pickuplat - dropofflat), 2)) AS dist,
  #Euclidean distance between pickup and drop off
  pickuplon - dropofflon AS londiff,
  pickuplat - dropofflat AS latdiff,
  passenger_count
  FROM taxi_preproc
  WHERE dataset < 3
```

Now let's create and train a model on this dataset. Run the following:

```sql
CREATE OR REPLACE MODEL
  taxi.taxifare_dnn OPTIONS (model_type='dnn_regressor',
    hidden_units=[144, 89, 55],
    labels=['fare_amount']) AS
SELECT
    fare_amount,
    hourofday,
    dayofweek,
    pickuplon,
    pickuplat,
    dropofflon,
    dropofflat,
    passenger_count
  FROM
    `taxi.taxi300k`
  WHERE
    dataset = 0;
```

BigQuery is now training a model based on a third of the rows representing our training dataset. The deep neural network has three layers with 144, 89, and 55 neurons respectively. This was determined mostly empirically and seems to be about the right order of magnitude to get good results (plus, they're all Fibonacci numbers, which suits the author...). How did it do? Click on the Evaluation tab to find out. A mean absolute error (MAE) less than 3 means we're predicting any taxi fare in NYC within 3 dollars on average--not bad for only a few minutes of training!

Now let's more formally evaluate the model. To do that, we'll run ML.EVALUATE against some of the rows that were not used in training.

```sql
SELECT
  SQRT(mean_squared_error) AS rmse
FROM
  ML.EVALUATE(MODEL taxi.taxifare_dnn, (SELECT
    fare_amount,
    hourofday,
    dayofweek,
    pickuplon,
    pickuplat,
    dropofflon,
    dropofflat,
    passenger_count
  FROM
    `taxi.taxi300k`
  WHERE
    dataset = 1
    ))
```

The model's predictions result in an RMSE near 5--again, not bad for only a few minutes of training on only 100k rows. Now let's make a few predictions using ML.PREDICT:

```sql
SELECT
    fare_amount,
    predicted_fare_amount,
    hourofday,
    dayofweek,
    pickuplon,
    pickuplat,
    dropofflon,
    dropofflat,
    passenger_count
FROM
  ML.PREDICT(MODEL taxi.taxifare_dnn, (SELECT
    fare_amount,
    hourofday,
    dayofweek,
    pickuplon,
    pickuplat,
    dropofflon,
    dropofflat,
    passenger_count
  FROM
    `taxi.taxi300k`
  WHERE
    dataset = 2
    ))
    LIMIT 10
```

To recap, we've been able to create a deep neural network model, evaluate it, and use it to make predictions in about 10 minutes with little more than basic knowledge of SQL and machine learning.