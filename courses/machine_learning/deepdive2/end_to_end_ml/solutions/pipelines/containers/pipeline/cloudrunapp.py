# Copyright 2020 Google, LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
from flask import Flask, request
import json
import os
import sys
import mlp_babyweight

app = Flask(__name__)

@app.route('/', methods=['POST'])
def process_newfile():
    req_data = request.get_json(force=True)
    print("Received {}".format(req_data))
    filename = req_data['filename']
    mlp_babyweight.finetune_and_deploy(filename)
    # Flush the stdout to avoid log buffering.
    sys.stdout.flush()
    return ('', 204)



if __name__ == '__main__':
    PORT = int(os.getenv('PORT')) if os.getenv('PORT') else 8080

    # This is used when running locally. Gunicorn is used to run the
    # application on Cloud Run. See entrypoint in Dockerfile.
    app.run(host='127.0.0.1', port=PORT, debug=True)
