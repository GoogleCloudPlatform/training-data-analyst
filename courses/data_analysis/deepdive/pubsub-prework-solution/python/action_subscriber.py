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
import entities_pb2
import threading
from action_utils import ActionUtils
from google.cloud import pubsub_v1


class ActionSubscriber:

  def __init__(self, project, subscription):
    self._subscriber = pubsub_v1.SubscriberClient()
    self._subscription_path = self._subscriber.subscription_path(
        project, subscription)
    self._subscribe_future = self._subscriber.subscribe(self._subscription_path,
                                                        self.callback)
    self._view_lock = threading.Lock()
    self._view_ids = set()

  def is_view_action(self, action):
    return action.action == entities_pb2.Action.VIEW

  def callback(self, message):
    self._view_lock.acquire()
    self._view_lock.release()
    action = ActionUtils.decode_action_from_json(message.data)
    try:
      if self.is_view_action(action):
        self._view_lock.acquire()
        self._view_ids.add(message.message_id)
        self._view_lock.release()
      message.ack()
    except Exception as e:
      print("ERROR " + str(e))

  def get_view_count(self):
    self._view_lock.acquire()
    view_count = len(self._view_ids)
    self._view_lock.release()
    return view_count
