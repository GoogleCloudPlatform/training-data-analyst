import apache_beam as beam

from apache_beam.io.gcp.datastore.v1new.datastoreio import ReadFromDatastore
from apache_beam.io.gcp.datastore.v1new.datastoreio import WriteToDatastore
from apache_beam.io.gcp.datastore.v1new.types import Entity
from apache_beam.io.gcp.datastore.v1new.types import Key
from apache_beam.io.gcp.datastore.v1new.types import Query
from apache_beam.options.pipeline_options import GoogleCloudOptions
from apache_beam.options.pipeline_options import PipelineOptions
from datetime import datetime

project = '[GCLOUD_PROJECT]' # Replace [GCLOUD_PROJECT] with project
kind = 'President'
options = PipelineOptions(project=project)

p = beam.Pipeline(options=options)
lines = p | 'Read from Cloud Storage' >> beam.io.ReadFromText('gs://[GCLOUD_BUCKET]/usa_presidents.csv') # Replace [GCLOUD_BUCKET] with Cloud Storage bucket
def to_entity(line):
  fields = line.split(',') #id,president,startYear,endYear,party,homeState,dateOfBirth
  id = int(fields[0])
  key = Key([kind,id])
  entity = Entity(key)
  president = fields[1]
  names = president.split(' ')
  entity.set_properties({'id': id,
                         'firstName': names[0],
                         'lastName': names[1],
                         'startYear': int(fields[2]),
                         'endYear': int(fields[3]),
                         'party': fields[4],
                         'homeState': fields[5],
                         'dateOfBirth': datetime.strptime(fields[6], '%Y-%m-%d')
                        })
  return entity
entities = lines | 'To Entity' >> beam.Map(to_entity)
entities | 'Write To Datastore' >> WriteToDatastore(project)
# lines | 'Write to Cloud Storage' >> beam.io.WriteToText('gs://[GCLOUD_BUCKET]/out')
p.run().wait_until_finish()
