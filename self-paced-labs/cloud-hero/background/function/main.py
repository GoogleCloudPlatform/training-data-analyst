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

""" This function handles messages posted to a pubsub topic by translating
    the data in the message as requested. The message must be a JSON encoded
    dictionary with fields:

    Original - the string to translate
    Language - the language to translate the string to

    The dictionary may have other fields, which will be ignored.
"""

# [START getting_started_background_translate_setup]
import base64
import hashlib
import json

from google.cloud import firestore
from google.cloud import translate
# [END getting_started_background_translate_setup]

# [START getting_started_background_translate_init]
# Get client objects once to reuse over multiple invocations.
xlate = translate.Client()
db = firestore.Client()
# [END getting_started_background_translate_init]


# [START getting_started_background_translate_string]
def translate_string(from_string, to_language):
    """ Translates a string to a specified language.

    from_string - the original string before translation

    to_language - the language to translate to, as a two-letter code (e.g.,
        'en' for english, 'de' for german)

    Returns the translated string and the code for original language
    """
    result = xlate.translate(from_string, target_language=to_language)
    return result['translatedText'], result['detectedSourceLanguage']
# [END getting_started_background_translate_string]


# [START getting_started_background_translate]
def document_name(message):
    """ Messages are saved in a Firestore database with document IDs generated
        from the original string and destination language. If the exact same
        translation is requested a second time, the result will overwrite the
        prior result.

        message - a dictionary with fields named Language and Original, and
            optionally other fields with any names

        Returns a unique name that is an allowed Firestore document ID
    """
    key = '{}/{}'.format(message['Language'], message['Original'])
    hashed = hashlib.sha512(key.encode()).digest()

    # Note that document IDs should not contain the '/' character
    name = base64.b64encode(hashed, altchars=b'+-').decode('utf-8')
    return name


@firestore.transactional
def update_database(transaction, message):
    name = document_name(message)
    doc_ref = db.collection('translations').document(document_id=name)

    try:
        doc_ref.get(transaction=transaction)
    except firestore.NotFound:
        return  # Don't replace an existing translation

    transaction.set(doc_ref, message)


def translate_message(event, context):
    """ Process a pubsub message requesting a translation
    """
    message_data = base64.b64decode(event['data']).decode('utf-8')
    message = json.loads(message_data)

    from_string = message['Original']
    to_language = message['Language']

    to_string, from_language = translate_string(from_string, to_language)

    message['Translated'] = to_string
    message['OriginalLanguage'] = from_language

    transaction = db.transaction()
    update_database(transaction, message)
# [END getting_started_background_translate]
