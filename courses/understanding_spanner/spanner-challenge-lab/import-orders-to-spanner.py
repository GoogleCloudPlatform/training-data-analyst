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


class OrderRow(NamedTuple):
    cust_id: int
    order_date: str
    order_num: str
    
beam.coders.registry.register_coder(OrderRow, beam.coders.RowCoder)


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
        default='orders.csv',
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
        default = 'orders',      
        help='Spanner table.')
    known_args, pipeline_args = parser.parse_known_args(argv)

    pipeline_options = PipelineOptions(pipeline_args)
    pipeline_options.view_as(SetupOptions).save_main_session = save_main_session

    with beam.Pipeline(options=pipeline_options) as p:
        orders = p | 'Read CSV to dataframe' >> read_csv(known_args.input)

        orders = ( convert.to_pcollection(orders)
            | 'Convert to OrderRow class' >> beam.Map(lambda x : OrderRow(**(x._asdict())))
            | 'Reverse bits in cust_id' >> beam.Map(lambda x : OrderRow(reverse_bits(x.cust_id), x.order_date, x.order_num))
        )

        orders | 'Write to Spanner' >> SpannerInsert(
                    project_id=projectid,
                    instance_id=known_args.instance,
                    database_id=known_args.database,
                    table=known_args.table)

        # Just for testing
        # orders | beam.Map(print)

if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  main()