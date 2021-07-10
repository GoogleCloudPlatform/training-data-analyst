# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

""" data_lake_to_mart.py demonstrates a Dataflow pipeline which reads a 
large BigQuery Table, joins in another dataset, and writes its contents to a 
BigQuery table.  
"""


import argparse
import logging
import os
import traceback

import apache_beam as beam
from apache_beam.io.gcp.bigquery import parse_table_schema_from_json
from apache_beam.options.pipeline_options import PipelineOptions


class DataLakeToDataMartCGBK:
    """A helper class which contains the logic to translate the file into 
    a format BigQuery will accept.
    
    This example uses CoGroupByKey to join two datasets together.
    """

    def __init__(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.schema_str = ''
        # This is the schema of the destination table in BigQuery.
        schema_file = os.path.join(dir_path, 'resources', 'orders_denormalized.json')
        with open(schema_file) \
                as f:
            data = f.read()
            # Wrapping the schema in fields is required for the BigQuery API.
            self.schema_str = '{"fields": ' + data + '}'

    def get_orders_query(self):
        """This returns a query against a very large fact table.  We are 
        using a fake orders dataset to simulate a fact table in a typical 
        data warehouse."""
        orders_query = """SELECT
            acct_number,
            col_number,
            col_number_1,
            col_number_10,
            col_number_100,
            col_number_101,
            col_number_102,
            col_number_103,
            col_number_104,
            col_number_105,
            col_number_106,
            col_number_107,
            col_number_108,
            col_number_109,
            col_number_11,
            col_number_110,
            col_number_111,
            col_number_112,
            col_number_113,
            col_number_114,
            col_number_115,
            col_number_116,
            col_number_117,
            col_number_118,
            col_number_119,
            col_number_12,
            col_number_120,
            col_number_121,
            col_number_122,
            col_number_123,
            col_number_124,
            col_number_125,
            col_number_126,
            col_number_127,
            col_number_128,
            col_number_129,
            col_number_13,
            col_number_130,
            col_number_131,
            col_number_132,
            col_number_133,
            col_number_134,
            col_number_135,
            col_number_136,
            col_number_14,
            col_number_15,
            col_number_16,
            col_number_17,
            col_number_18,
            col_number_19,
            col_number_2,
            col_number_20,
            col_number_21,
            col_number_22,
            col_number_23,
            col_number_24,
            col_number_25,
            col_number_26,
            col_number_27,
            col_number_28,
            col_number_29,
            col_number_3,
            col_number_30,
            col_number_31,
            col_number_32,
            col_number_33,
            col_number_34,
            col_number_35,
            col_number_36,
            col_number_37,
            col_number_38,
            col_number_39,
            col_number_4,
            col_number_40,
            col_number_41,
            col_number_42,
            col_number_43,
            col_number_44,
            col_number_45,
            col_number_46,
            col_number_47,
            col_number_48,
            col_number_49,
            col_number_5,
            col_number_50,
            col_number_51,
            col_number_52,
            col_number_53,
            col_number_54,
            col_number_55,
            col_number_56,
            col_number_57,
            col_number_58,
            col_number_59,
            col_number_6,
            col_number_60,
            col_number_61,
            col_number_62,
            col_number_63,
            col_number_64,
            col_number_65,
            col_number_66,
            col_number_67,
            col_number_68,
            col_number_69,
            col_number_7,
            col_number_70,
            col_number_71,
            col_number_72,
            col_number_73,
            col_number_74,
            col_number_75,
            col_number_76,
            col_number_77,
            col_number_78,
            col_number_79,
            col_number_8,
            col_number_80,
            col_number_81,
            col_number_82,
            col_number_83,
            col_number_84,
            col_number_85,
            col_number_86,
            col_number_87,
            col_number_88,
            col_number_89,
            col_number_9,
            col_number_90,
            col_number_91,
            col_number_92,
            col_number_93,
            col_number_94,
            col_number_95,
            col_number_96,
            col_number_97,
            col_number_98,
            col_number_99,
            col_number_num1,
            date,
            foo,
            num1,
            num2,
            num3,
            num5,
            num6,
            product_number,
            quantity
        FROM
            `python-dataflow-example.example_data.orders` orders
        LIMIT
            10  
        """
        return orders_query

    def add_account_details(self, account_info):
        """This function performs the join of the two datasets."""
        (acct_number, data) = account_info
        result = list(data['orders'])
        if not data['account_details']:
            logging.info('account details are empty')
            return
        if not data['orders']:
            logging.info('orders are empty')
            return

        account_details = {}
        try:
            account_details = data['account_details'][0]
        except KeyError as err:
            traceback.print_exc()
            logging.error("Account Not Found error: %s", err)

        for order in result:
            order.update(account_details)

        return result


def run(argv=None):
    """The main function which creates the pipeline and runs it."""
    parser = argparse.ArgumentParser()
    # Here we add some specific command line arguments we expect.
    # This defaults the output table in your BigQuery you'll have
    # to create the example_data dataset yourself using bq mk temp
    parser.add_argument('--output', dest='output', required=False,
                        help='Output BQ table to write results to.',
                        default='lake.orders_denormalized_cogroupbykey')

    # Parse arguments from the command line.
    known_args, pipeline_args = parser.parse_known_args(argv)

    # DataLakeToDataMartCGBK is a class we built in this script to hold the logic for
    # transforming the file into a BigQuery table.  It also contains an example of
    # using CoGroupByKey
    data_lake_to_data_mart = DataLakeToDataMartCGBK()

    schema = parse_table_schema_from_json(data_lake_to_data_mart.schema_str)
    pipeline = beam.Pipeline(options=PipelineOptions(pipeline_args))

    # This query returns details about the account, normalized into a
    # different table.  We will be joining the data in to the main orders dataset in order
    # to create a denormalized table.
    account_details_source = (
        pipeline
        | 'Read Account Details from BigQuery ' >> beam.io.Read(
            beam.io.BigQuerySource(query="""
                SELECT
                  acct_number,
                  acct_company_name,
                  acct_group_name,
                  acct_name,
                  acct_org_name,
                  address,
                  city,
                  state,
                  zip_code,
                  country
                FROM
                  `python-dataflow-example.example_data.account`
            """, use_standard_sql=True))
        # This next stage of the pipeline maps the acct_number to a single row of
        # results from BigQuery.  Mapping this way helps Dataflow move your data arround
        # to different workers.  When later stages of the pipeline run, all results from
        # a given account number will run on one worker.
        | 'Map Account to Order Details' >> beam.Map(
            lambda row: (
                row['acct_number'], row
            )))

    orders_query = data_lake_to_data_mart.get_orders_query()
    # Read the orders from BigQuery.  This is the source of the pipeline.  All further
    # processing starts with rows read from the query results here.
    orders = (
        pipeline
        | 'Read Orders from BigQuery ' >> beam.io.Read(
            beam.io.BigQuerySource(query=orders_query, use_standard_sql=True))
        |
        # This next stage of the pipeline maps the acct_number to a single row of
        # results from BigQuery.  Mapping this way helps Dataflow move your data around
        # to different workers.  When later stages of the pipeline run, all results from
        # a given account number will run on one worker.
        'Map Account to Account Details' >> beam.Map(
            lambda row: (
                row['acct_number'], row
            )))

    # CoGroupByKey allows us to arrange the results together by key
    # Both "orders" and "account_details" are maps of
    # acct_number -> "Row of results from BigQuery".
    # The mapping is done in the above code using Beam.Map()
    result = {'orders': orders, 'account_details': account_details_source} | \
             beam.CoGroupByKey()
    # The add_account_details function is responsible for defining how to
    # join the two datasets.  It passes the results of CoGroupByKey, which
    # groups the data from the same key in each dataset together in the same
    # worker.
    joined = result | beam.FlatMap(data_lake_to_data_mart.add_account_details)
    joined | 'Write Data to BigQuery' >> beam.io.Write(
        beam.io.BigQuerySink(
            # The table name is a required argument for the BigQuery sink.
            # In this case we use the value passed in from the command line.
            known_args.output,
            # Here we use the JSON schema read in from a JSON file.
            # Specifying the schema allows the API to create the table correctly if it does not yet exist.
            schema=schema,
            # Creates the table in BigQuery if it does not yet exist.
            create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
            # Deletes all data in the BigQuery table before writing.
            write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE))

    pipeline.run().wait_until_finish()


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run()
