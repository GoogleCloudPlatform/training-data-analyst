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
from google.cloud import spanner

spanner_client = spanner.Client()
instance = spanner_client.instance('quiz-instance')
database = instance.database('quiz-database')

"""
Takes an email address and reverses it (to be used as primary key)
"""
def reverse_email(email):
    return '_'.join(list(reversed(email.replace('@','_').
                        replace('.','_').
                        split('_'))))

def save_answer(data):
    with database.batch() as batch:
        answer_id = '{}_{}_{}'.format(reverse_email(data['email']),
                                        data['quiz'],
                                        data['timestamp'])
        batch.insert(
            table='answers',
            columns=(
                'answerId',
                'id',
                'email',
                'quiz',
                'answer',
                'correct',
                'timestamp'
            ),
            values=[
                (
                    answer_id,
                    data['id'],
                    data['email'],
                    data['quiz'],
                    data['answer'],
                    data['correct'],
                    data['timestamp']
                )
            ]
        )