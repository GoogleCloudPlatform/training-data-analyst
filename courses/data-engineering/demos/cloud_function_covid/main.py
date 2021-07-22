# Copyright 2020 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# Script to set up necessary packages and run tweet-gatherer script.
# User needs to update TODOs starting on line 29.


# event and context are two variables provided by the Cloud Function invocation
def update_va_covid(event, context):
    
    #TODO: Replace project ID with your project ID.
    PROJECT_ID = 'insert-your-project-here'

    import pandas as pd
    from datetime import date, timedelta, datetime
    from google.cloud import bigquery

    start_date = date(2020, 5, 1)
    end_date = datetime.now().date()
    delta = timedelta(days=1)

    li = []

    print('Importing file for {}'.format(start_date))

    file_loc = 'https://data.virginia.gov/api/views/8bkr-zfqv/rows.csv'

    df = pd.read_csv(file_loc, index_col=None, header=0)

    col_list = ['Number of Cases', 'Number of Testing Encounters',
                'Number of PCR Testing Encounters']

    for col in col_list:
        df[col] = df[col].replace('Suppressed*', '')

    df.to_csv('/tmp/preproc_va_zip_data.csv')

    print('Imported files.')

    print('Saved concatenated files.')

    client = bigquery.Client()

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=True,
        write_disposition='WRITE_TRUNCATE'
    )

    table_id = "{}.covid19.va_covid_data_by_zip".format(PROJECT_ID)

    with open('/tmp/preproc_va_zip_data.csv', "rb") as source_file:
        job = client.load_table_from_file(source_file, table_id,
                                          job_config=job_config)

    job.result()

    table = client.get_table(table_id)
    print(
        "Loaded {} rows and {} columns to {}".format(
            table.num_rows, len(table.schema), table_id
        )
    )
