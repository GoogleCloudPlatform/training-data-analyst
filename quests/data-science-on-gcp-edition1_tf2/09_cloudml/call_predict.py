#!/usr/bin/env python3

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
import argparse
import json

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--project", required=True,
                    help="Project that flights service is deployed in")
args = parser.parse_args()

credentials = GoogleCredentials.get_application_default()
api = discovery.build('ml', 'v1', credentials=credentials,
            discoveryServiceUrl='https://storage.googleapis.com/cloud-ml/discovery/ml_v1_discovery.json')

request_data = {'instances':
  [
      {
        'dep_delay': 16.0,
        'taxiout': 13.0,
        'distance': 160.0,
        'avg_dep_delay': 13.34,
        'avg_arr_delay': 67.0,
        'carrier': 'AS',
        'dep_lat': 61.17,
        'dep_lon': -150.00,
        'arr_lat': 60.49,
        'arr_lon': -145.48,
        'origin': 'ANC',
        'dest': 'CDV'
      }
  ]
}

PROJECT = args.project
parent = 'projects/%s/models/%s/versions/%s' % (PROJECT, 'flights', 'tf2')
response = api.projects().predict(body=request_data, name=parent).execute()
print("response={0}".format(response))
