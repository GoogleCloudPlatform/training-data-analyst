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

import re
import uuid

import main
import pytest


@pytest.fixture
def client():
    """ Yields a test client, AND creates and later cleans up a
        dummy collection for sessions.
    """
    main.app.testing = True

    # Override the Firestore collection used for sessions in main
    main.sessions = main.db.collection(str(uuid.uuid4()))

    client = main.app.test_client()
    yield client

    # Clean up session objects created in test collection
    for doc_ref in main.sessions.list_documents():
        doc_ref.delete()


def test_session(client):
    r = client.get('/')
    assert r.status_code == 200
    data = r.data.decode('utf-8')
    assert '1 views' in data

    match = re.search('views for ([A-Za-z ]+)', data)
    assert match is not None
    greeting = match.group(1)

    r = client.get('/')
    assert r.status_code == 200
    data = r.data.decode('utf-8')
    assert '2 views' in data
    assert greeting in data
