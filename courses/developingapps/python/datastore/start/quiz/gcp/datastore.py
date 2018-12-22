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

# TODO: Import the os module

import os

# END TODO

# TODO: Get the GCLOUD_PROJECT environment variable

project_id = os.getenv('GCLOUD_PROJECT')

# END TODO

from flask import current_app

# TODO: Import the datastore module from the google.cloud package

from google.cloud import datastore

# END TODO

# TODO: Create a Cloud Datastore client object
# The datastore client object requires the Project ID.
# Pass through the Project ID you looked up from the
# environment variable earlier

datastore_client = datastore.Client(project_id)

# END TODO

"""
Returns a list of question entities for a given quiz
- filter by quiz name, defaulting to gcp
- no paging
- add in the entity key as the id property 
- if redact is true, remove the correctAnswer property from each entity
"""

# def list_entities(quiz='gcp', redact=True):
#     return [{'quiz':'gcp', 'title':'Sample question', 'answer1': 'A', 'answer2': 'B', 'answer3': 'C', 'answer4': 'D', 'correctAnswer': 1, 'author': 'Nigel'}]
def list_entities(quiz='gcp', redact=True):
    query = datastore_client.query(kind='Question')
    query.add_filter('quiz', '=', quiz)
    results =list(query.fetch())
    for result in results:
        result['id'] = result.key.id
    if redact:
        for result in results:
            del result['correctAnswer']
    return results

"""
Create and persist and entity for each question
The Datastore key is the equivalent of a primary key in a relational database.
There are two main ways of writing a key:
1. Specify the kind, and let Datastore generate a unique numeric id
2. Specify the kind and a unique string id
"""
def save_question(question):
    # TODO: Create a key for a Datastore entity whose kind is Question
    
    key = datastore_client.key('Question')
    

    # END TODO

    # TODO: Create a Datastore entity object using the key

    q_entity = datastore.Entity(key=key)

    # END TODO

    # TODO: Iterate over the form values supplied to the function

    for q_prop, q_val in question.iteritems():

        # END TODO

        # TODO: Assign each key and value to the Datastore entity

        q_entity[q_prop] = q_val


    # END TODO


    # TODO: Save the entity

    datastore_client.put(q_entity)

    # END TODO