# ai-for-time-series

This course contains a set of labs demonstrating how to use the Cloud AI Platform (CAIP) to solve time-series forecasting problems.

Lab 1: [Creating and Visualizing a Time-Series Data Set](notebooks/01-explore.ipynb)
* Tools: BigQuery, Google Cloud Storage, CAIP Notebooks
* Topics:
  * Visualizing time-series data
  * Sampling frequency
  * Key issues in time-series data (stationarity, seasonality, etc.)
  * Univariate vs multivariate time series

Lab 2: [Building a Custom Time Series Forecasting Model](notebooks/02-model.ipynb)
* Tools: CAIP Notebooks, TensorFlow
* Topics:
  * Long Short Term Networks (LSTM)
  * Convolutional Neural Networks (CNN)
  * Statistical modeling approaches (ARIMA, Exponential smoothing)
  * Handling missing values

Lab 3: [Training and Predicting with a Cloud Model](notebooks/03-cloud-training.ipynb)
* Tools: CAIP Notebooks, CAIP Training, CAIP Prediction
* Topics:
  * Prepare data and models for training in the cloud
  * Train your model and monitor the progress of the job with AI Platform Training
  * Predict using the model with AI Platform Predictions