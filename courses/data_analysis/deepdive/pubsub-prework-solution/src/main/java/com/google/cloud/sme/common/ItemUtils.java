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

public class ItemUtils {
  /**
   * Takes a string of the form item ID,size,color,type,price and parses it into an Entities.Item
   * object. If the string is not of the proper format, null is returned.
   */
  public static Entities.Item parseFromCSVLine(String line) {
    String[] parts = line.split(",");
    if (parts.length != 5) {
      return null;
    }

    Long id;
    try {
      id = Long.parseLong(parts[0]);
    } catch (NumberFormatException e) {
      System.err.println("Could not parse ID: " + e);
      return null;
    }

    Double price;
    try {
      price = Double.parseDouble(parts[4]);
    } catch (NumberFormatException e) {
      System.err.println("Could not parse price: " + e);
      return null;
    }

    Entities.Item item =
        Entities.Item.newBuilder()
            .setId(id)
            .setSize(parts[1])
            .setColor(parts[2])
            .setType(parts[3])
            .setPrice(price)
            .build();
    return item;
  }

  /** Takes CSV content from stream and returns a map from item IDs to the Item objects. */
  public static Map<Long, Entities.Item> parseFromCSV(Stream<String> stream) {
    return stream.map(i -> parseFromCSVLine(i)).collect(Collectors.toMap(i -> i.getId(), i -> i));
  }

  /** Encodes an Item in a format suitable for transmission as a Google Cloud Pub/Sub message. */
  public static ByteString encodeItem(Entities.Item item) {
    return item.toByteString();
  }

  /**
   * Decodes an Item from the contents of a Google Cloud Pub/Sub message. Returns null if the string
   * could not be parsed.
   */
  public static Entities.Item decodeItem(ByteString str) {
    try {
      return Entities.Item.parseFrom(str);
    } catch (Exception e) {
      return null;
    }
  }

  /** Encodes an Item in JSON format. */
  public static ByteString encodeItemAsJson(Entities.Item item) {
    try {
      return ByteString.copyFromUtf8(JsonFormat.printer().print(item));
    } catch (Exception e) {
      return null;
    }
  }

  /** Decodes an Item from JSON. Returns null if the string could not be parsed. */
  public static Entities.Item decodeItemFromJson(ByteString str) {
    try {
      Entities.Item.Builder builder = Entities.Item.newBuilder();
      JsonFormat.parser().merge(str.toStringUtf8(), builder);
      return builder.build();
    } catch (Exception e) {
      return null;
    }
  }
}
