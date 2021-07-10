# Copyright 2015 Google Inc.
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

import contextlib

import bookshelf
from conftest import flaky_filter
from flaky import flaky
import mock
from oauth2client.client import OAuth2Credentials
import pytest


@pytest.fixture
def client_with_credentials(app):
    """This fixture provides a Flask app test client that has a session
    pre-configured with use credentials."""
    credentials = OAuth2Credentials(
        'access_token',
        'client_id',
        'client_secret',
        'refresh_token',
        '3600',
        None,
        'Test',
        id_token={'sub': '123', 'email': 'user@example.com'},
        scopes=('email', 'profile'))

    @contextlib.contextmanager
    def inner():
        with app.test_client() as client:
            with client.session_transaction() as session:
                session['profile'] = {
                    'email': 'abc@example.com',
                    'name': 'Test User'
                }
                session['google_oauth2_credentials'] = credentials.to_json()
            yield client

    return inner


# Mark all test cases in this class as flaky, so that if errors occur they
# can be retried. This is useful when databases are temporarily unavailable.
@flaky(rerun_filter=flaky_filter)
# Tell pytest to use both the app and model fixtures for all test cases.
# This ensures that configuration is properly applied and that all database
# resources created during tests are cleaned up. These fixtures are defined
# in conftest.py
@pytest.mark.usefixtures('app', 'model')
class TestAuth(object):
    def test_not_logged_in(self, app):
        with app.test_client() as c:
            rv = c.get('/books/')

        assert rv.status == '200 OK'
        body = rv.data.decode('utf-8')
        assert 'Login' in body

    def test_logged_in(self, client_with_credentials):
        with client_with_credentials() as c:
            rv = c.get('/books/')

        assert rv.status == '200 OK'
        body = rv.data.decode('utf-8')
        assert 'Test User' in body

    def test_add_anonymous(self, app):
        data = {
            'title': 'Test Book',
        }

        with app.test_client() as c:
            rv = c.post('/books/add', data=data, follow_redirects=True)

        assert rv.status == '200 OK'
        body = rv.data.decode('utf-8')
        assert 'Test Book' in body
        assert 'Added by Anonymous' in body

    def test_add_logged_in(self, client_with_credentials):
        data = {
            'title': 'Test Book',
        }

        with client_with_credentials() as c:
            rv = c.post('/books/add', data=data, follow_redirects=True)

        assert rv.status == '200 OK'
        body = rv.data.decode('utf-8')
        assert 'Test Book' in body
        assert 'Added by Test User' in body

    def test_mine(self, model, client_with_credentials):
        # Create two books, one created by the logged in user and one
        # created by another user.
        model.create({
            'title': 'Book 1',
            'createdById': 'abc@example.com'
        })

        model.create({
            'title': 'Book 2',
            'createdById': 'def@example.com'
        })

        # Check the "My Books" page and make sure only one of the books
        # appears.
        with client_with_credentials() as c:
            rv = c.get('/books/mine')

        assert rv.status == '200 OK'
        body = rv.data.decode('utf-8')
        assert 'Book 1' in body
        assert 'Book 2' not in body

    @mock.patch("httplib2.Http")
    def test_request_user_info(self, HttpMock):
        httpObj = mock.MagicMock()
        responseMock = mock.MagicMock(status=200)
        httpObj.request = mock.MagicMock(
            return_value=(responseMock, b'{"name": "bill"}'))
        HttpMock.return_value = httpObj
        credentials = mock.MagicMock()
        bookshelf._request_user_info(credentials)
