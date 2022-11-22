import argparse
import logging
import re, os
from typing import NamedTuple

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions
from apache_beam.io.gcp.spanner import ReadFromSpanner

class PetRow(NamedTuple):
    PetName: str
    PetType: str
    Breed: str

beam.coders.registry.register_coder(PetRow, beam.coders.RowCoder)

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

  # The pipeline will be run on exiting the with block.
    with beam.Pipeline(options=pipeline_options) as p:
        owner_pets = p | ReadFromSpanner(
                            project_id=projectid,
                            instance_id='test-spanner-instance',
                            database_id='pets-db',
                            row_type=PetRow,
                            sql='SELECT * FROM Pets',
                            ).with_output_types(PetRow)
        owner_pets | beam.Map(print)  
    # regions = (
    #           p | 'Read Regions' >> ReadFromText(regionsfilename)
    #             | 'Parse Regions' >> beam.ParDo(RegionParseTuple())
    #           )
    # regions | 'Print Regions' >> beam.Map(print)
        
    # territories = (
    #               p | 'Read Territories' >> ReadFromText('territories.csv')
    #                 | 'Parse Territories' >> beam.ParDo(TerritoryParseTuple())
    #               )
    # territories | 'Print Territories' >> beam.Map(print)

    # nested = ( 
    #     {'regions':regions, 'territories':territories} 
    #           | 'Nest territories into regions' >> beam.CoGroupByKey()
    #           | 'Reshape to dict' >> beam.Map(lambda x : {'regionid': x[0], 'regionname': x[1]['regions'][0], 
    #                                                      'territories': x[1]['territories']})
    #           | 'Sort by territoryid' >> beam.ParDo(SortTerritories())
    # )
    # nested | 'Print' >> beam.Map(print)
    # nested | 'Write nested region_territory to BQ' >> beam.io.WriteToBigQuery('region_territory', dataset = 'dataflow'
    #                                                                          , project = PROJECT_ID
    #                                                                          , method = 'BATCH_LOAD'
    #                                                                          )

if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  main()
