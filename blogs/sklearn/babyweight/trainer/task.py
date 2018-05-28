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
        help = 'output directory for model, automatically provided by gcloud',
        required = True
    )
    
    args = parser.parse_args()
    arguments = args.__dict__
    
    model.PROJECT = arguments['projectId']
    model.KEYDIR  = 'trainer'
    
    estimator, rmse = model.train_and_evaluate(arguments['frac'],
                                         arguments['maxDepth'],
                                         arguments['numTrees']
                                        )
    loc = model.save_model(estimator, 
                           arguments['job_dir'], 'babyweight')
    print("Saved model to {}".format(loc))
    
    # this is for hyperparameter tuning
    from tensorflow.core.framework.summary_pb2 import Summary
    import tensorflow as tf
    with tf.Session() as sess:
      summary = Summary(value=[Summary.Value(tag='rmse', simple_value=rmse)])
      eval_path = os.path.join(arguments['job_dir'], 'rmse')
      summary_writer = tf.summary.FileWriter(eval_path)
      summary_writer.add_summary(summary)
      summary_writer.flush()

# done