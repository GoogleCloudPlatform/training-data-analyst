import logging
import re
from google.cloud import storage
import joblib
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer
import pandas as pd
from xgboost import XGBRegressor

def read_input(file_name, test_size=0.25):
  """Read input data and split it into train and test."""

  if file_name.startswith("gs://"):
    gcs_path = file_name
    train_bucket_name, train_path = split_gcs_uri(gcs_path)

    storage_client = storage.Client()
    train_bucket = storage_client.get_bucket(train_bucket_name)
    train_blob = train_bucket.blob(train_path)

    file_name = "/tmp/data.csv"
    train_blob.download_to_filename(file_name)

  data = pd.read_csv(file_name)
  data.dropna(axis=0, subset=['SalePrice'], inplace=True)

  y = data.SalePrice
  X = data.drop(['SalePrice'], axis=1).select_dtypes(exclude=['object'])

  train_X, test_X, train_y, test_y = train_test_split(X.values,
                                                    y.values,
                                                    test_size=test_size,
                                                    shuffle=False)

  imputer = SimpleImputer()
  train_X = imputer.fit_transform(train_X)
  test_X = imputer.transform(test_X)

  return (train_X, train_y), (test_X, test_y)

def load_model(model_path):
  local_model_path = model_path

  if model_path.startswith("gs://"):
    gcs_path = model_path
    train_bucket_name, train_path = split_gcs_uri(gcs_path)

    storage_client = storage.Client()
    train_bucket = storage_client.get_bucket(train_bucket_name)
    train_blob = train_bucket.blob(train_path)

    local_model_path = "/tmp/model.dat"
    logging.info("Downloading model to %s", local_model_path)
    train_blob.download_to_filename(local_model_path)

  model = joblib.load(local_model_path)
  return model

def train_model(train_X,
                train_y,
                test_X,
                test_y,
                n_estimators,
                learning_rate):
  """Train the model using XGBRegressor."""
  model = XGBRegressor(n_estimators=n_estimators, learning_rate=learning_rate)

  model.fit(train_X,
          train_y,
          early_stopping_rounds=40,
          eval_set=[(test_X, test_y)])

  logging.info("Best RMSE on eval: %.2f with %d rounds",
               model.best_score,
               model.best_iteration+1)
  return model

def eval_model(model, test_X, test_y):
  """Evaluate the model performance."""
  predictions = model.predict(test_X)
  logging.info("mean_absolute_error=%.2f", mean_absolute_error(predictions, test_y))

def save_model(model, model_file):
  """Save XGBoost model for serving."""

  gcs_path = None
  if model_file.startswith("gs://"):
    gcs_path = model_file
    model_file = "/tmp/model.dat"
  joblib.dump(model, model_file)
  logging.info("Model export success: %s", model_file)

  if gcs_path:
    model_bucket_name, model_path = split_gcs_uri(gcs_path)
    storage_client = storage.Client()
    model_bucket = storage_client.get_bucket(model_bucket_name)
    model_blob = model_bucket.blob(model_path)

    logging.info("Uploading model to %s", gcs_path)
    model_blob.upload_from_filename(model_file)

def split_gcs_uri(gcs_uri):
  """Split a GCS URI into bucket and path."""
  GCS_REGEX = re.compile("gs://([^/]*)(/.*)?")
  m = GCS_REGEX.match(gcs_uri)
  bucket = m.group(1)
  path = ""
  if m.group(2):
    path = m.group(2).lstrip("/")
  return bucket, path
