# Copyright 2018 Google Inc. All Rights Reserved.
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
import argparse
import os

import model

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--bucket',
        help = 'GCS path to output.',
        required = True
    )
    parser.add_argument(
        '--frac',
        help = 'Fraction of input to process',
        type = float,
        required = True
    )
    parser.add_argument(
        '--maxDepth',
        help = 'Depth of trees',
        type = int,
        default = 5
    )
    parser.add_argument(
        '--numTrees',
        help = 'Number of trees',
        type = int,
        default = 100
    )
    parser.add_argument(
        '--projectId',
        help = 'ID (not name) of your project',
        required = True
    )
    parser.add_argument(
        '--job-dir',
        help = 'this model ignores this field, but it is required by gcloud',
        default = 'junk'
    )
    
    args = parser.parse_args()
    arguments = args.__dict__
    
    model.PROJECT = arguments['projectId']
    model.KEYDIR  = 'trainer'
    
    estimator = model.train_and_evaluate(arguments['frac'],
                                         arguments['maxDepth'],
                                         arguments['numTrees']
                                        )
    loc = model.save_model(estimator, 
                           'gs://{}/babyweight/sklearn'.format(arguments['bucket']), 'babyweight')
    print("Saved model to {}".format(loc))

# done