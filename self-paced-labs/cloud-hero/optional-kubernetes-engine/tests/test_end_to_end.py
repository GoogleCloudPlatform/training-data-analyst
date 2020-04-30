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

import os
import re

from bs4 import BeautifulSoup
import pytest
import requests
from retrying import retry


@pytest.mark.e2e
def test_end_to_end():
    """Tests designed to be run against live environments.

    Unlike the integration tests in the other packages, these tests are
    designed to be run against fully-functional live environments.

    To run locally, start both main.py and psq_worker main.books_queue and
    run this file.

    It can be run against a live environment by setting the E2E_URL
    environment variables before running the tests:

        E2E_URL=http://your-app-id.appspot.com \
        nosetests tests/test_end_to_end.py
    """

    base_url = os.environ.get('E2E_URL', 'http://localhost:8080')

    book_data = {
        'title': 'a confederacy of dunces',
    }

    response = requests.post(base_url + '/books/add', data=book_data)

    # There was a 302, so get the book's URL from the redirect.
    book_url = response.request.url
    book_id = book_url.rsplit('/', 1).pop()

    # Use retry because it will take some indeterminate time for the pub/sub
    # message to be processed.
    @retry(wait_exponential_multiplier=5000, stop_max_attempt_number=12)
    def check_for_updated_data():
        # Check that the book's information was updated.
        response = requests.get(book_url)
        assert response.status_code == 200

        soup = BeautifulSoup(response.text, 'html.parser')

        title = soup.find('h4', 'book-title').contents[0].strip()
        assert re.search(r'A Confederacy of Dunces', title, re.I)

        author = soup.find('h5', 'book-author').string
        assert re.search(r'John Kennedy Toole', author, re.I)

        description = soup.find('p', 'book-description').string
        assert re.search(r'Ignatius', description, re.I)

        image_src = soup.find('img', 'book-image')['src']
        image = requests.get(image_src)
        assert image.status_code == 200

    try:
        check_for_updated_data()
    finally:
        # Delete the book we created.
        requests.get(base_url + '/books/{}/delete'.format(book_id))
