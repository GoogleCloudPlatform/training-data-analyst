// Copyright 2017 Google Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
////////////////////////////////////////////////////////////////////////////////
package com.google.cloud.sme.common;

import com.google.cloud.sme.Entities;
import com.google.protobuf.ByteString;
import com.google.protobuf.Timestamp;
import com.google.protobuf.util.JsonFormat;
import java.util.stream.Stream;

public class ActionUtils {
  /**
   * Takes a string of the form timestamp,user ID,action,item ID and parses it into an
   * Entities.Action object. If the string is not of the proper format, null is returned.
   */
  public static Entities.Action parseFromCSVLine(String line) {
    String[] parts = line.split(",");
    if (parts.length != 4) {
      return null;
    }

    Long userId, itemId, timestampSeconds;
    try {
      timestampSeconds = Long.parseLong(parts[0]);
      userId = Long.parseLong(parts[1]);
      itemId = Long.parseLong(parts[3]);
    } catch (NumberFormatException e) {
      System.err.println("Could not parse: " + e);
      return null;
    }

    Timestamp timestamp = Timestamp.newBuilder().setSeconds(timestampSeconds).build();

    Entities.Action.ActionType type = Entities.Action.ActionType.valueOf(parts[2]);

    Entities.Action action =
        Entities.Action.newBuilder()
            .setAction(type)
            .setUserId(userId)
            .setItemId(itemId)
            .setTime(timestamp)
            .build();

    return action;
  }

  /** Takes CSV content from stream and returns a stream of actions. */
  public static Stream<Entities.Action> parseFromCSV(Stream<String> stream) {
    return stream.map(a -> parseFromCSVLine(a));
  }

  /** Encodes an Action in a format suitable for transmission as a Google Cloud Pub/Sub message. */
  public static ByteString encodeAction(Entities.Action action) {
    return action.toByteString();
  }

  /**
   * Decodes an Action from the contents of a Google Cloud Pub/Sub message. Returns null if the
   * string could not be parsed.
   */
  public static Entities.Action decodeAction(ByteString str) {
    try {
      return Entities.Action.parseFrom(str);
    } catch (Exception e) {
      return null;
    }
  }

  /** Encodes an Action in JSON format. */
  public static ByteString encodeActionAsJson(Entities.Action action) {
    try {
      return ByteString.copyFromUtf8(JsonFormat.printer().print(action));
    } catch (Exception e) {
      return null;
    }
  }

  /** Decodes an Action from JSON. Returns null if the string could not be parsed. */
  public static Entities.Action decodeActionFromJson(ByteString str) {
    try {
      Entities.Action.Builder builder = Entities.Action.newBuilder();
      JsonFormat.parser().merge(str.toStringUtf8(), builder);
      return builder.build();
    } catch (Exception e) {
      return null;
    }
  }
}
