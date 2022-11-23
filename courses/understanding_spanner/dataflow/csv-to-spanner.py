import argparse
import logging
import re, os
from typing import NamedTuple, List

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions
from apache_beam.io.gcp.spanner import SpannerInsert
from apache_beam.dataframe.io import read_csv
from apache_beam.dataframe import convert

class PetRow(NamedTuple):
    PetID: int
    OwnerID: int
    PetName: str
    PetType: str
    Breed: str
beam.coders.registry.register_coder(PetRow, beam.coders.RowCoder)

def reverse_bits(num, bitSize = 32):
    binary = bin(num)
    reverse = binary[-1:1:-1]
    reverse = reverse + (bitSize - len(reverse))*'0'
    return int(reverse,2)

def main(argv=None, save_main_session=True):
    """Main entry point."""
    projectid = os.environ.get('GOOGLE_CLOUD_PROJECT')
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--input',
        dest='input',
        default='pets.csv',
        help='Input filename.')
    parser.add_argument(
        '--instance',
        dest='instance',
        default='test-spanner-instance',
        help='Spanner instance ID.')
    parser.add_argument(
        '--database',
        dest='database',
        default = 'pets-db',      
        help='Spanner database.')
    parser.add_argument(
        '--table',
        dest='table',
        default = 'pets',      
        help='Spanner table.')
    known_args, pipeline_args = parser.parse_known_args(argv)

    pipeline_options = PipelineOptions(pipeline_args)
    pipeline_options.view_as(SetupOptions).save_main_session = save_main_session

    with beam.Pipeline(options=pipeline_options) as p:
        pets = p | 'Read CSV to dataframe' >> read_csv(known_args.input)
        pets = ( convert.to_pcollection(pets)
            | 'Convert to PetRow class' >> beam.Map(lambda x : PetRow(**(x._asdict())))
            | 'Reverse bits in PetID' >> beam.Map(lambda x : PetRow(reverse_bits(x.PetID), reverse_bits(x.OwnerID), x.PetName, x.PetType, x.Breed))
        )
        pets | 'Write to Spanner' >> SpannerInsert(
                    project_id=projectid,
                    instance_id=known_args.instance,
                    database_id=known_args.database,
                    table=known_args.table)

        pets | beam.Map(print)

if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  main()

