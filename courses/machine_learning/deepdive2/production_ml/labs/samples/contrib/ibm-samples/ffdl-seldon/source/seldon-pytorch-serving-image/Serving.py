#
# Copyright 2017-2018 IBM Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import torch
import boto3
import botocore
import os
import zipfile
import importlib


class Serving(object):
    def __init__(self):
        training_id = os.environ.get("TRAINING_ID")
        endpoint_url = os.environ.get("BUCKET_ENDPOINT_URL")
        bucket_name = os.environ.get("BUCKET_NAME")
        bucket_key = os.environ.get("BUCKET_KEY")
        bucket_secret = os.environ.get("BUCKET_SECRET")
        model_file_name = os.environ.get("MODEL_FILE_NAME")
        model_class_name = os.environ.get("MODEL_CLASS_NAME")
        model_class_file = os.environ.get("MODEL_CLASS_FILE")


        # Uncomment the below print statement for debugging purpose.
        # print("Training id:{} endpoint URL:{} key:{} secret:{}".format(training_id,endpoint_url,bucket_key,bucket_secret))

        # Define S3 resource and download the model files
        client = boto3.resource(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=bucket_key,
            aws_secret_access_key=bucket_secret,
        )

        KEY = training_id + '/' + model_file_name
        model_files = training_id + '/_submitted_code/model.zip'

        try:
            client.Bucket(bucket_name).download_file(KEY, 'model.pt')
            client.Bucket(bucket_name).download_file(model_files, 'model.zip')
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                print("The object does not exist.")
            else:
                raise

        zip_ref = zipfile.ZipFile('model.zip', 'r')
        zip_ref.extractall('model_files')
        zip_ref.close()

        modulename = 'model_files.' + model_class_file.split('.')[0].replace('-', '_')

        '''
        We required users to define where the model class is located or follow
        some naming convention we have provided.
        '''
        model_class = getattr(importlib.import_module(modulename), model_class_name)
        self.model = model_class()
        self.model.load_state_dict(torch.load("model.pt"))
        self.model.eval()

    def predict(self, X, feature_names):
        return self.model(X)
