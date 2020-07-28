import apache_beam as beam
from datetime import datetime
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.io.gcp.datastore.v1new.datastoreio import ReadFromDatastore
from apache_beam.io.gcp.datastore.v1new.datastoreio import WriteToDatastore
from apache_beam.io.gcp.datastore.v1new.datastoreio import types

project = '[GCLOUD_PROJECT]' # Replace [GCLOUD_PROJECT] with project
kind = 'President'

options = PipelineOptions(project=project)
p = beam.Pipeline(options=options)
lines = p | 'Read from Cloud Storage' >> beam.io.ReadFromText('gs://[GCLOUD_PROJECT]/usa_presidents.csv') # Replace [GCLOUD_BUCKET] with Cloud Storage bucket

def to_entity(line):
  fields = line.split(',') #id,president,startYear,endYear,party,homeState,dateOfBirth
  id = fields[0]
  president = fields[1]
  names = president.split(' ')
  firstName = names[0]
  lastName = names[1]
  startYear = fields[2]
  endYear = fields[3]
  party = fields[4]
  homeState = fields[5]
  dateOfBirth = fields[6]

  entity = types.Entity(key=types.Key([kind, str(id)]))
  
  entity.set_properties({'firstName':firstName,
    'lastName': lastName, 
    'startYear': int(startYear), 
    'endYear': int(endYear), 
    'party': party, 
    'homeState': homeState, 
    'dateOfBirth': datetime.strptime(dateOfBirth, '%Y-%m-%d') })
  return entity

entities = lines | 'To Entity' >> beam.Map(to_entity)
entities | 'Write To Datastore' >> WriteToDatastore(project)
# lines | 'Write to Cloud Storage' >> beam.io.WriteToText('gs://[GCLOUD_BUCKET]/out')

p.run().wait_until_finish()
