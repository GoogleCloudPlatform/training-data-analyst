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


class ProductRow(NamedTuple):
    prod_code: int
    prod_name: str
    prod_desc: str
    prod_price: float

beam.coders.registry.register_coder(ProductRow, beam.coders.RowCoder)

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
        default='products.csv',
        help='Input filename.')
    parser.add_argument(
        '--instance',
        dest='instance',
        default='challenge-lab-instance',
        help='Spanner instance ID.')
    parser.add_argument(
        '--database',
        dest='database',
        default = 'orders-db',      
        help='Spanner database.')
    parser.add_argument(
        '--table',
        dest='table',
        default = 'products',      
        help='Spanner table.')
    known_args, pipeline_args = parser.parse_known_args(argv)

    pipeline_options = PipelineOptions(pipeline_args)
    pipeline_options.view_as(SetupOptions).save_main_session = save_main_session

    with beam.Pipeline(options=pipeline_options) as p:
        products = p | 'Read CSV to dataframe' >> read_csv(known_args.input)

        products = ( convert.to_pcollection(products)
            | 'Convert to ProductRow class' >> beam.Map(lambda x : ProductRow(**(x._asdict())))
            | 'Reverse bits in prod_code' >> beam.Map(lambda x : ProductRow(reverse_bits(x.prod_code), x.prod_name, x.prod_desc, x.prod_price))
        )

        products | 'Write to Spanner' >> SpannerInsert(
                    project_id=projectid,
                    instance_id=known_args.instance,
                    database_id=known_args.database,
                    table=known_args.table)

        # Just for testing
        # products | beam.Map(print)

if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  main()