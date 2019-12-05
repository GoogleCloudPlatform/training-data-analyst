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

import base64
import json

from google.cloud import firestore
import main


def clear_collection(collection):
    """ Removes every document from the collection, to make it easy to see
        what has been added by the current test run.
    """
    for doc in collection.stream():
        doc.reference.delete()


def test_invocations():
    db = firestore.Client()
    main.db = db

    translations = db.collection('translations')
    clear_collection(translations)

    event = {
        'data': base64.b64encode(json.dumps({
            'Original': 'My test message',
            'Language': 'de',
        }).encode('utf-8'))
    }

    main.translate_message(event, None)

    docs = [doc for doc in translations.stream()]
    assert len(docs) == 1   # Should be only the one just created

    message = docs[0].to_dict()

    assert message['Original'] == 'My test message'
    assert message['Language'] == 'de'
    assert len(message['Translated']) > 0
    assert message['OriginalLanguage'] == 'en'
