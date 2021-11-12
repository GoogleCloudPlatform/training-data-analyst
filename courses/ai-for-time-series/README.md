# ai-for-time-series

This course contains a set of labs demonstrating how to use Vertex AI to solve time-series forecasting problems.

Lab 1: [Creating and Visualizing a Time-Series Data Set](notebooks/01-explore.ipynb)
* Tools: Google Cloud Storage, Vertex AI Workbench
* Topics:
  * Visualizing time-series data
  * Sampling frequency
  * Key issues in time-series data (stationarity, seasonality, etc.)
  * Univariate vs multivariate time series

Lab 2: [Building a Custom Time Series Forecasting Model](notebooks/02-model.ipynb)
* Tools: Vertex AI Workbench, TensorFlow
* Topics:
  * Long Short Term Networks (LSTM)
  * Convolutional Neural Networks (CNN)
  * Statistical modeling approaches (ARIMA, Exponential smoothing)
  * Handling missing values

Lab 3: [Training and Predicting with a Cloud Model](notebooks/03-cloud-training.ipynb)
* Tools: Vertex AI Workbench, Vertex AI Training, Vertex AI Prediction
* Topics:
  * Prepare data and models for training in the cloud
  * Train your model and monitor the progress of the job with Vertex AI Training
  * Predict using the model with Vertex AI Predictions
