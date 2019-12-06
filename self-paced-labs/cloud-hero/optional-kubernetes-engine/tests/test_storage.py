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

import re

from conftest import flaky_filter
from flaky import flaky
import httplib2
import pytest
from six import BytesIO


# Mark all test cases in this class as flaky, so that if errors occur they
# can be retried. This is useful when databases are temporarily unavailable.
@flaky(rerun_filter=flaky_filter)
# Tell pytest to use both the app and model fixtures for all test cases.
# This ensures that configuration is properly applied and that all database
# resources created during tests are cleaned up. These fixtures are defined
# in conftest.py
@pytest.mark.usefixtures('app', 'model')
class TestStorage(object):

    def test_upload_image(self, app):
        data = {
            'title': 'Test Book',
            'author': 'Test Author',
            'publishedDate': 'Test Date Published',
            'description': 'Test Description',
            'image': (BytesIO(b'hello world'), 'hello.jpg')
        }

        with app.test_client() as c:
            rv = c.post('/books/add', data=data, follow_redirects=True)

        assert rv.status == '200 OK'
        body = rv.data.decode('utf-8')

        img_tag = re.search('<img.*?src="(.*)"', body).group(1)

        http = httplib2.Http()
        resp, content = http.request(img_tag)
        assert resp.status == 200
        assert content == b'hello world'

    def test_upload_bad_file(self, app):
        data = {
            'title': 'Test Book',
            'author': 'Test Author',
            'publishedDate': 'Test Date Published',
            'description': 'Test Description',
            'image': (BytesIO(b'<?php phpinfo(); ?>'),
                      '1337h4x0r.php')
        }

        with app.test_client() as c:
            rv = c.post('/books/add', data=data, follow_redirects=True)

        # check we weren't pwned
        assert rv.status == '400 BAD REQUEST'
