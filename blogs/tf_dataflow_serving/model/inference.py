import tensorflow as tf
import os
import logging
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

tf.logging.set_verbosity(tf.logging.ERROR)

SAVED_MODEL_DIR = 'trained/v1'
PROJECT = '<PROJECT_ID>'
CMLE_MODEL_NAME = 'babyweight_estimator'
CMLE_MODEL_VERSION = 'v1'


#[START inference_local]
predictor_fn = None


def init_predictor():
    """ Loads the TensorFlow saved model to the predictor object

    Returns:
        predictor_fn
    """

    global predictor_fn

    if predictor_fn is None:

        logging.info("Initialising predictor...")
        dir_path = os.path.dirname(os.path.realpath(__file__))
        export_dir = os.path.join(dir_path, SAVED_MODEL_DIR)

        if os.path.exists(export_dir):
            predictor_fn = tf.contrib.predictor.from_saved_model(
                export_dir=export_dir,
                signature_def_key="predict"
            )
        else:
            logging.error("Model not found! - Invalid model path: {}".format(export_dir))


def estimate_local(instances):
    """
    Calls the local babyweight estimator to get predictions

    Args:
       instances: list of json objects
    Returns:
        int - estimated baby weight
    """

    init_predictor()

    inputs = dict((k, [v]) for k, v in instances[0].items())
    for i in range(1,len(instances)):
        instance = instances[i]

        for k, v in instance.items():
            inputs[k] += [v]

    values = predictor_fn(inputs)['predictions']
    return [value.item() for value in values.reshape(-1)]
#[END inference_local]


#[START inference_cmle]
cmle_api = None

def init_api():

    global cmle_api

    if cmle_api is None:
        cmle_api = discovery.build('ml', 'v1',
                              discoveryServiceUrl='https://storage.googleapis.com/cloud-ml/discovery/ml_v1_discovery.json',
                              cache_discovery=True)


def estimate_cmle(instances):
    """
    Calls the babyweight estimator API on CMLE to get predictions

    Args:
       instances: list of json objects
    Returns:
        int - estimated baby weight
    """
    init_api()

    request_data = {'instances': instances}

    model_url = 'projects/{}/models/{}/versions/{}'.format(PROJECT, CMLE_MODEL_NAME, CMLE_MODEL_VERSION)
    response = cmle_api.projects().predict(body=request_data, name=model_url).execute()
    values = [item["predictions"][0] for item in response['predictions']]
    return values
#[END inference_cmle]
