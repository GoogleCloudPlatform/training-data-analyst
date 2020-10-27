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
from action_utils import ActionUtils
from google.cloud import pubsub_v1


# A basic Pub/Sub publisher for purposes of demonstrating use of the API.
class ActionPublisher:
  # Creates a new publisher associated with the given project and topic.
  def __init__(self, project, topic):
    self._publisher = pubsub_v1.PublisherClient()
    self._topic_path = self._publisher.topic_path(project, topic)

  def callback(self, message_future):
    # When timeout is unspecified, the exception method waits indefinitely.
    if message_future.exception(timeout=30):
      print('Publishing message on {} threw an Exception {}.'.format(
          topic_name, message_future.exception()))

  # Publishes the action on the topic associated with this publisher.
  def publish(self, action):
    data = ActionUtils.encode_action_as_json(action)
    data = data.encode('utf-8')

    message_future = self._publisher.publish(self._topic_path, data=data)
    message_future.add_done_callback(self.callback)
