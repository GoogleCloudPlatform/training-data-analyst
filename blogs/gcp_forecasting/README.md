## How to quickly solve machine learning forecasting problems using Pandas and BigQuery

Read more about this solution in the [article](TODO).

Below is a good workflow for tackling forecasting problems:

1. Create features and labels on a subsample of data using Pandas and train an initial model locally
2. Create features and labels on the full dataset using BigQuery
3. Utilize BigQuery ML to build a scalable machine learning model
4. (Advanced) Build a forecasting model using Recurrent Neural Networks in Keras and TensorFlow

The notebook `[gcp_time_series_forecasting](gcp_time_series_forecasting.ipynb)` provides an end-to-end walkthrough of these steps.

The `time_series.py` and `scalable_time_series.py` files show how to create sliding window features and labels using Pandas and BigQuery respectively.

![](rolling_window.gif)