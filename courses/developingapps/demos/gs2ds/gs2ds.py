from google.cloud.proto.datastore.v1 import entity_pb2
from google.cloud.proto.datastore.v1 import query_pb2
import googledatastore
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.io.gcp.datastore.v1.datastoreio import ReadFromDatastore
from apache_beam.io.gcp.datastore.v1.datastoreio import WriteToDatastore

project = 'qwiklabs-gcp-0f0e1e5dcaa28938'
kind = 'Question'

# runner = 'DataflowRunner'
runner = 'DirectRunner'

options = PipelineOptions(project=project)
p = beam.Pipeline(options=options)
lines = p | 'Read from Cloud Storage' >> beam.io.ReadFromText('gs://gs2ds-demo/questions.csv')

def to_entity(line):
  entity = entity_pb2.Entity()
  fields = line.split(',') # id,author,quiz,question,answer1,answer2,answer3,answer4,correctAnswer
  id = fields[0]
  author = fields[1]
  quiz = fields[2]
  question = fields[3]
  answer1 = fields[4]
  answer2 = fields[5]
  answer3 = fields[6]
  answer4 = fields[7]
  correctAnswer = fields[8]
  googledatastore.helper.add_key_path(entity.key, kind, str(id))
  googledatastore.helper.add_properties(entity, {'author': unicode(author), 'quiz': unicode(quiz), 'question': unicode(question), 'answer1': unicode(an
swer1), 'answer2': unicode(answer2), 'answer3': unicode(answer3), 'answer4': unicode(answer4), 'correctAnswer': unicode(correctAnswer)})
  return entity

entities = lines | 'To Entity' >> beam.Map(to_entity)
entities | 'Write To Datastore' >> WriteToDatastore(project)
# lines | 'Write to Cloud Storage' >> beam.io.WriteToText('gs://gs2ds-demo/out')

p.run().wait_until_finish()