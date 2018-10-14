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
import entities_pb2
from google.protobuf import timestamp_pb2
from google.protobuf import json_format

class ActionUtils:
  @staticmethod
  def parse_from_csv_line(line):
    parts = line.split(",")
    if len(parts) < 3 or len(parts) > 4:
      return False

    user_id = -1
    item_id = -1
    timestamp_seconds = -1
    try:
      user_id = int(parts[1])
    except ValueError:
      print("Could not parse: " + parts[1])
      return False
    try:
      timestamp_seconds = int(parts[0])
    except ValueError:
      print("Could not parse: " + parts[0])
      return False
    if len(parts) == 4:
      try:
        item_id = int(parts[3])
      except ValueError:
        print("Could not parse: " + parts[3])
        return False

    timestamp = timestamp_pb2.Timestamp()
    timestamp.seconds = timestamp_seconds

    action = entities_pb2.Action()
    action.action = entities_pb2.Action.ActionType.Value(parts[2])
    action.user_id = user_id
    if item_id != -1:
      action.item_id = item_id
    action.time.seconds = timestamp_seconds
    return action

  @staticmethod
  def parse_from_csv(file):
    with open(file) as fp:
     for _, line in enumerate(fp):
      yield ActionUtils.parse_from_csv_line(line)

  @staticmethod
  def encode_action(action):
    return action.SerializeToString()

  @staticmethod
  def decode_action(str):
    action = entities_pb2.Action()
    return action.ParseFromString(str)

  @staticmethod
  def encode_action_as_json(action):
    return json_format.MessageToJson(action)

  @staticmethod
  def decode_action_from_json(str):
    action = entities_pb2.Action()
    return json_format.Parse(str, action)
