# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
###############################################################################
import argparse
import time
from action_publisher import ActionPublisher
from action_subscriber import ActionSubscriber
from action_utils import ActionUtils

# A basic Pub/Sub example for demonstrating use of the API.

parser = argparse.ArgumentParser(
    description='Publish and subscribe to Cloud Pub/Sub.')
parser.add_argument(
    '-i',
    '--input',
    nargs='?',
    required=True,
    help='The file from which to grab the events to publish.')
parser.add_argument(
    '-p',
    '--project',
    nargs='?',
    required=True,
    help='The Google Cloud Pub/Sub project in which the topic exists.')
parser.add_argument(
    '-t',
    '--topic',
    nargs='?',
    required=True,
    help='The Google Cloud Pub/Sub topic name to which to publish.')
parser.add_argument(
    '-s',
    '--subscription',
    nargs='?',
    required=True,
    help='The Google Cloud Pub/Sub subscriber name on which to subscribe.')

args = parser.parse_args()

subscriber = ActionSubscriber(args.project, args.subscription)

publisher = ActionPublisher(args.project, args.topic)

for a in ActionUtils.parse_from_csv(args.input):
  publisher.publish(a)

time.sleep(10)

print('View action count: {}'.format(subscriber.get_view_count()))
