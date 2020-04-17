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

import random
from uuid import uuid4

from flask import Flask, make_response, request
from google.cloud import firestore


app = Flask(__name__)
db = firestore.Client()
sessions = db.collection('sessions')
greetings = [
    'Hello World',
    'Hallo Welt',
    'Ciao Mondo',
    'Salut le Monde',
    'Hola Mundo',
]


@firestore.transactional
def get_session_data(transaction, session_id):
    """ Looks up (or creates) the session with the given session_id.
        Creates a random session_id if none is provided. Increments
        the number of views in this session. Updates are done in a
        transaction to make sure no saved increments are overwritten.
    """
    if session_id is None:
        session_id = str(uuid4())   # Random, unique identifier

    doc_ref = sessions.document(document_id=session_id)
    doc = doc_ref.get(transaction=transaction)
    if doc.exists:
        session = doc.to_dict()
    else:
        session = {
            'greeting': random.choice(greetings),
            'views': 0
        }

    session['views'] += 1   # This counts as a view
    transaction.set(doc_ref, session)

    session['session_id'] = session_id
    return session


@app.route('/', methods=['GET'])
def home():
    template = '<body>{} views for {}</body>'

    transaction = db.transaction()
    session = get_session_data(transaction, request.cookies.get('session_id'))

    resp = make_response(template.format(
        session['views'],
        session['greeting']
        )
    )
    resp.set_cookie('session_id', session['session_id'], httponly=True)
    return resp


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080)
