# Copyright 2020 Google LLC. All Rights Reserved.
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
"""The pipeline configurations.
"""

import os

class Config:
    """Sets configuration vars."""
    
    PIPELINE_NAME=os.getenv("PIPELINE_NAME", "covertype_continuous_training")
    MODEL_NAME=os.getenv("MODEL_NAME", "covertype_classifier")
    PROJECT_ID=os.getenv("PROJECT_ID", "mlops-workshop")
    GCP_REGION=os.getenv("GCP_REGION", "us-central1")
    TFX_IMAGE=os.getenv("KUBEFLOW_TFX_IMAGE", "tensorflow/tfx:0.21.4")
    DATA_ROOT_URI=os.getenv("DATA_ROOT_URI", "gs://workshop-datasets/covertype/small")
    ARTIFACT_STORE_URI=os.getenv("ARTIFACT_STORE_URI", "gs://mlops-workshop-artifact-store")
    RUNTIME_VERSION=os.getenv("RUNTIME_VERSION", "2.1")
    PYTHON_VERSION=os.getenv("PYTHON_VERSION", "3.7")
    USE_KFP_SA=os.getenv("USE_KFP_SA", "False")
    
    
    