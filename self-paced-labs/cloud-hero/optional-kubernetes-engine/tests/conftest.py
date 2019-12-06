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

"""conftest.py is used to define common test fixtures for pytest."""

import bookshelf
import config
from google.cloud.exceptions import ServiceUnavailable
from oauth2client.client import HttpAccessTokenRefreshError
import pytest
from retrying import retry


@pytest.yield_fixture(params=['datastore', 'mongodb'])
def app(request):
    """This fixtures provides a Flask app instance configured for testing.

    Because it's parametric, it will cause every test that uses this fixture
    to run three times: one time for each backend (datastore, cloudsql, and
    mongodb).

    It also ensures the tests run within a request context, allowing
    any calls to flask.request, flask.current_app, etc. to work."""
    app = bookshelf.create_app(
        config,
        testing=True,
        config_overrides={
            'DATA_BACKEND': request.param
        })

    with app.test_request_context():
        yield app


@pytest.yield_fixture
def model(monkeypatch, app):
    """This fixture provides a modified version of the app's model that tracks
    all created items and deletes them at the end of the test.

    Any tests that directly or indirectly interact with the database should use
    this to ensure that resources are properly cleaned up.

    Monkeypatch is provided by pytest and used to patch the model's create
    method.

    The app fixture is needed to provide the configuration and context needed
    to get the proper model object.
    """
    model = bookshelf.get_model()

    # Ensure no books exist before running. This typically helps if tests
    # somehow left the database in a bad state.
    delete_all_books(model)

    yield model

    # Delete all books that we created during tests.
    delete_all_books(model)


# The backend data stores can sometimes be flaky. It's useful to retry this
# a few times before giving up.
@retry(
    stop_max_attempt_number=3,
    wait_exponential_multiplier=100,
    wait_exponential_max=2000)
def delete_all_books(model):
    while True:
        books, _ = model.list(limit=50)
        if not books:
            break
        for book in books:
            model.delete(book['id'])


def flaky_filter(info, *args):
    """Used by flaky to determine when to re-run a test case."""
    _, e, _ = info
    return isinstance(e, (ServiceUnavailable, HttpAccessTokenRefreshError))
