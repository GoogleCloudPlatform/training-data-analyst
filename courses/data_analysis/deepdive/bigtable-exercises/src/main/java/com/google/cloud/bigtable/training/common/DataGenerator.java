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

package com.google.cloud.bigtable.training.common;

import java.time.Duration;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;
import java.util.Random;
import java.util.function.Consumer;

/**
 * Generate time series data that we will store in Bigtable.
 */
public class DataGenerator {
  public static final String SERVICE_ID_FIELD = "service";
  public static final String METRIC_FIELD = "metric";
  public static final String TIMESTAMP_FIELD = "timestamp";
  public static final String VALUE_FIELD = "value";
  public static final String TAGS_FIELD = "tags"; // Contains a Map<String, String>

  private static final int NUM_SERVICES = 100;

  // Generate data points starting at "duration" time units in the past.
  // Invoke the consumer for each point.
  public static void consumeRandomData(Duration duration, Consumer<Map<String, Object>> consumer) {
    // Data points every 60 seconds
    long batches = duration.getSeconds() / 60;

    Date start = new Date(System.currentTimeMillis() - duration.toMillis());

    Random r = new Random();
    for (int i = 0; i < batches; i++) {
      long timestamp = start.getTime() + i * 60_000;
      for (int j = 0; j < NUM_SERVICES; j++) {
        Map<String, String> tags = new HashMap<>();
        String service = "service-" + j;
        tags.put("environment", j % 4 == 0 ? "dev" : "prod");
        if (j % 5 == 0) {
          tags.put("experiment", j % 2 == 0 ? "group-A" : "group-B");
        }

        consumer.accept(newPoint(service, "qps", r.nextInt(10000), tags, timestamp));
        consumer.accept(newPoint(service, "latency", r.nextDouble(), tags, timestamp));
      }
    }
  }

  private static Map<String, Object> newPoint(String service, String metric,
      Object value, Map<String, String> tags, long timestamp) {
    Map<String, Object> point = new HashMap<>();
    point.put(TIMESTAMP_FIELD, timestamp);
    point.put(SERVICE_ID_FIELD, service);
    point.put(METRIC_FIELD, metric);
    point.put(TAGS_FIELD, tags);
    point.put(VALUE_FIELD, value);
    return point;
  }
}
