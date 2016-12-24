bq show --format=prettyjson flights.simevents > simevents.json


bq mk --external_table_definition=./tzcorr.json@CSV=gs://cloud-training-demos-ml/flights/tzcorr/all_flights-00030-of-00036 flights.fedtzcorr

bq load flights.tzcorr "gs://cloud-training-demos-ml/flights/tzcorr/all_flights-*" tzcorr.json
