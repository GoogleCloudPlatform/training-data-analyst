# Copyright 2017 Google Inc.
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

import re

# TODO: Import the spanner module

from google.cloud import spanner

# END TODO

"""
Get spanner management objects
"""

# TODO: Create a spanner Client

spanner_client = spanner.Client()

# END TODO


# TODO: Get a reference to the Cloud Spanner quiz-instance

instance = spanner_client.instance('quiz-instance')

# END TODO

# TODO: Get a referent to the Cloud Spanner quiz-database

database = instance.database('quiz-database')

# END TODO

"""
Takes an email address and reverses it (to be used as primary key)
"""
def reverse_email(email):
    return '_'.join(list(reversed(email.replace('@','_').
                        replace('.','_').
                        split('_'))))

"""
Persists feedback data into Spanner
- create primary key value
- do a batch insert (even though it's a single record)
"""
def save_feedback(data):
    # TODO: Create a batch object for database operations

    with database.batch() as batch:
        # TODO: Create a key for the record
        # from the email, quiz and timestamp

        feedback_id = '{}_{}_{}'.format(reverse_email(data['email']),
                                        data['quiz'],
                                        data['timestamp'])

        # END TODO

        # TODO: Use the batch to insert a record
        # into the feedback table
        # This needs the columns and values

        batch.insert(
            table='feedback',
            columns=(
                'feedbackId',
                'email',
                'quiz',
                'timestamp',
                'rating',
                'score',
                'feedback'
            ),
            values=[
                (
                    feedback_id,
                    data['email'],
                    data['quiz'],
                    data['timestamp'],
                    data['rating'],
                    data['score'],
                    data['feedback']
                )
            ]
        )

        # END TODO

    # END TODO

