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


# A basic Pub/Sub subscriber for purposes of demonstrating use of the API.
class ActionSubscriber:
  # Creates a new subscriber associated with the given project and subscription.
  def __init__(self, project, subscription):
    return

  # Returns the number of VIEW action seen
  def get_view_count(self):
    return -1

  # Returns true if action is a VIEW action.
  def is_view_action(self, action):
    return action.action == entities_pb2.Action.VIEW
