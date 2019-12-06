# Copyright 2019 Google LLC All Rights Reserved.
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

""" This web app shows translations that have been previously requested, and
    provides a form to request a new translation.
"""

# [START getting_started_background_app_main]
import json
import os

from flask import Flask, redirect, render_template, request
from google.cloud import firestore
from google.cloud import pubsub


app = Flask(__name__)

# Get client objects to reuse over multiple invocations
db = firestore.Client()
publisher = pubsub.PublisherClient()

# Keep this list of supported languages up to date
ACCEPTABLE_LANGUAGES = ('de', 'en', 'es', 'fr', 'ja', 'sw')
# [END getting_started_background_app_main]


# [START getting_started_background_app_list]
@app.route('/', methods=['GET'])
def index():
    """ The home page has a list of prior translations and a form to
        ask for a new translation.
    """

    doc_list = []
    docs = db.collection('translations').stream()
    for doc in docs:
        doc_list.append(doc.to_dict())

    return render_template('index.html', translations=doc_list)
# [END getting_started_background_app_list]


# [START getting_started_background_app_request]
@app.route('/request-translation', methods=['POST'])
def translate():
    """ Handle a request to translate a string (form field 'v') to a given
        language (form field 'lang'), by sending a PubSub message to a topic.
    """
    source_string = request.form.get('v', '')
    to_language = request.form.get('lang', '')

    if source_string == '':
        error_message = 'Empty value'
        return error_message, 400

    if to_language not in ACCEPTABLE_LANGUAGES:
        error_message = 'Unsupported language: {}'.format(to_language)
        return error_message, 400

    message = {
        'Original': source_string,
        'Language': to_language,
        'Translated': '',
        'OriginalLanguage': '',
    }

    topic_name = 'projects/{}/topics/{}'.format(
        os.getenv('GOOGLE_CLOUD_PROJECT'), 'translate'
    )
    publisher.publish(topic_name, json.dumps(message).encode('utf8'))
    return redirect('/')
# [END getting_started_background_app_request]
