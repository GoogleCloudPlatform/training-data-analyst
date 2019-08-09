import tensorflow as tf
from google.cloud import bigquery

PROJECT_ID = 'qwiklabs-gcp-da02053fb2a13c97'

class TaxifarePredictor(object):
    def __init__(self, predict_fn):
      self.predict_fn = predict_fn   
    
    def predict(self, instances, **kwargs):
        bq = bigquery.Client(PROJECT_ID)
        query_string = """
        SELECT
          *
        FROM
          `taxifare.traffic_realtime`
        ORDER BY
          time DESC
        LIMIT 1
        """
        trips = bq.query(query_string).to_dataframe()['trips_last_5min'][0]
        instances['trips_last_5min'] = [trips for _ in range(len(list(instances.items())[0][1]))]
        predictions = self.predict_fn(instances)
        return predictions['predictions'].tolist() # convert to list so it is JSON serialiable (requirement)
    

    @classmethod
    def from_path(cls, model_dir):
        predict_fn = tf.contrib.predictor.from_saved_model(model_dir,'predict')
        return cls(predict_fn)
