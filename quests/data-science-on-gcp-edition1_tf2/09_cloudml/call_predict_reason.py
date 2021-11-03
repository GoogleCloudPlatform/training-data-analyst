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
        'dep_delay': dep_delay,
        'taxiout': taxiout,
        'distance': 160.0,
        'avg_dep_delay': 13.34,
        'avg_arr_delay': avg_arr_delay,
        'carrier': 'AS',
        'dep_lat': 61.17,
        'dep_lon': -150.00,
        'arr_lat': 60.49,
        'arr_lon': -145.48,
        'origin': 'ANC',
        'dest': 'CDV'
      }
      for dep_delay, taxiout, avg_arr_delay in
        [[16.0, 13.0, 67.0],
         [13.3, 13.0, 67.0], # if dep_delay was the airport mean
         [16.0, 16.0, 67.0], # if taxiout was the global mean
         [16.0, 13.0, 4] # if avg_arr_delay was the global mean
        ]
  ]
}

PROJECT = args.project
parent = 'projects/%s/models/%s/versions/%s' % (PROJECT, 'flights', 'tf2')
response = api.projects().predict(body=request_data, name=parent).execute()
print("response={}".format(response))

probs = [pred[u'pred'][0] for pred in response[u'predictions']]
print("probs={}".format(probs))

# find the maximal impact variable
max_impact = 0.3  # unless impact of var > 0.3, we'll go with 'typical'
max_impact_factor =  0
for factor in range(1, len(probs)):
   impact = abs(probs[factor] - probs[0])
   if impact > max_impact:
      max_impact = impact
      max_impact_factor = factor

reasons = ["this flight appears rather typical",
           "the departure delay is typically 13.3 minutes",
           "the taxiout time is typically 16.0 minutes",
           "the avg_arrival_delay is typically 4 minutes"]

print("\n\nThe ontime probability={}; the key reason is that {} {}".format(
           probs[0],
           reasons[max_impact_factor],
           "-- had it been typical, the ontime probability would have been {}".format(probs[max_impact_factor]) if max_impact_factor > 0 else ""
      ))

