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
import com.google.protobuf.util.JsonFormat;
import java.util.Map;
import java.util.stream.Collectors;
import java.util.stream.Stream;

public class UserUtils {
  /**
   * Takes a string of the form user ID,first name,last name,country and parses it into an
   * Entities.User object. If the string is not of the proper format, null is returned.
   */
  public static Entities.User parseFromCSVLine(String line) {
    String[] parts = line.split(",");
    if (parts.length != 4) {
      return null;
    }

    Long id;
    try {
      id = Long.parseLong(parts[0]);
    } catch (NumberFormatException e) {
      System.err.println("Could not parse ID: " + e);
      return null;
    }

    Entities.User user =
        Entities.User.newBuilder()
            .setId(id)
            .setFirstName(parts[1])
            .setLastName(parts[2])
            .setCountry(parts[3])
            .build();

    return user;
  }

  /** Takes CSV content from stream and returns a map from user IDs to the User objects. */
  public static Map<Long, Entities.User> parseFromCSV(Stream<String> stream) {
    return stream.map(u -> parseFromCSVLine(u)).collect(Collectors.toMap(u -> u.getId(), u -> u));
  }

  /** Encodes a User in a format suitable for transmission as a Google Cloud Pub/Sub message. */
  public static ByteString encodeUser(Entities.User user) {
    return user.toByteString();
  }

  /**
   * Decodes a User from the contents of a Google Cloud Pub/Sub message. Returns null if the string
   * could not be parsed.
   */
  public static Entities.User decodeUser(ByteString str) {
    try {
      return Entities.User.parseFrom(str);
    } catch (Exception e) {
      return null;
    }
  }

  /** Encodes a user in JSON format. */
  public static ByteString encodeuserAsJson(Entities.User user) {
    try {
      return ByteString.copyFromUtf8(JsonFormat.printer().print(user));
    } catch (Exception e) {
      return null;
    }
  }

  /** Decodes a User from JSON. Returns null if the string could not be parsed. */
  public static Entities.User decodeUserFromJson(ByteString str) {
    try {
      Entities.User.Builder builder = Entities.User.newBuilder();
      JsonFormat.parser().merge(str.toStringUtf8(), builder);
      return builder.build();
    } catch (Exception e) {
      return null;
    }
  }
}
