import argparse
import logging
import re, os
from typing import NamedTuple, List

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions
from apache_beam.io.gcp.spanner import ReadFromSpanner


class PetRow(NamedTuple):
    OwnerID: str
    PetName: str
    PetType: str
    Breed: str

beam.coders.registry.register_coder(PetRow, beam.coders.RowCoder)

class Owner_PetRow(NamedTuple):
    Owner: str
    Pets: List[PetRow]
beam.coders.registry.register_coder(Owner_PetRow, beam.coders.RowCoder)


def main(argv=None, save_main_session=True):
    """Main entry point."""
    projectid = os.environ.get('GOOGLE_CLOUD_PROJECT')
    parser = argparse.ArgumentParser()
#   parser.add_argument(
#       '--input',
#       dest='input',
#       default=f'gs://{projectid}/regions.csv',
#       help='Input file to process.')
#   parser.add_argument(
#       '--output',
#       dest='output',
#       default = f'gs://{projectid}/regions_output',      
#       help='Output file to write results to.')
    known_args, pipeline_args = parser.parse_known_args(argv)

    pipeline_options = PipelineOptions(pipeline_args)
    pipeline_options.view_as(SetupOptions).save_main_session = save_main_session

    with beam.Pipeline(options=pipeline_options) as p:
        owner_pets = p | ReadFromSpanner(
                            project_id=projectid,
                            instance_id='test-spanner-instance',
                            database_id='pets-db',
                            row_type=PetRow,
                            sql = "SELECT OwnerID, PetName, PetType, Breed FROM Pets"
#                            sql='SELECT o.OwnerName, ARRAY_AGG(STRUCT<string, string, string>(p.PetName, p.PetType, p.Breed)) AS Pets FROM Owners as o JOIN Pets AS p ON o.OwnerID = p.OwnerID GROUP BY o.OwnerName',
                            ).with_output_types(PetRow)
                            
        ( owner_pets | beam.Map(lambda x : x._asdict())
                     | beam.io.WriteToBigQuery('Pets', dataset = 'petsdb', project = projectid, method = 'STREAMING_INSERTS')
        )
        owner_pets | beam.Map(print)  

if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  main()
