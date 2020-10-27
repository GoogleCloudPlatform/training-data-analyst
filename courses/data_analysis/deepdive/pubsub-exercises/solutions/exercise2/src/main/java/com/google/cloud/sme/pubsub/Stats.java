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
package com.google.cloud.sme.pubsub;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import org.joda.time.DateTime;

/** Stats collection for latency and throughput designed to avoid contention */
public class Stats {
  private class ThreadLocalLong {
    public long size;
  }

  private ScheduledExecutorService executor = Executors.newScheduledThreadPool(10);

  private List<List<Long>> allLatencies = new ArrayList<List<Long>>();
  private List<ThreadLocalLong> allSizes = new ArrayList<ThreadLocalLong>();

  private long startTime = 0;
  private long endTime = 0;

  private final ThreadLocal<List<Long>> tLatencies =
      new ThreadLocal<List<Long>>() {
        @Override
        protected List<Long> initialValue() {
          ArrayList<Long> list = new ArrayList<Long>();
          synchronized (allLatencies) {
            allLatencies.add(list);
          }
          return list;
        }
      };

  public Map<Double, Long> getLatencies() {
    Map<Double, Long> pctLatencies = new HashMap<Double, Long>();
    List<Long> combinedLatencies = new ArrayList<Long>();
    for (List<Long> latencies : allLatencies) {
      combinedLatencies.addAll(latencies);
    }
    Collections.sort(combinedLatencies);
    pctLatencies.put(50.0, combinedLatencies.get(combinedLatencies.size() / 2));
    pctLatencies.put(99.0, combinedLatencies.get((int) (0.99 * combinedLatencies.size())));
    pctLatencies.put(99.9, combinedLatencies.get((int) (0.999 * combinedLatencies.size())));
    return pctLatencies;
  }

  public long getThroughputMessages() {
    return getMessageCount() / ((endTime - startTime) / 1000);
  }

  public long getMessageCount() {
    long messageCount = 0;
    for (List<Long> latencies : allLatencies) {
      messageCount += latencies.size();
    }
    return messageCount;
  }

  public void start() {
    startTime = DateTime.now().getMillis();
  }

  public void stop(long lastEventTime) {
    endTime = lastEventTime;
  }

  public void recordLatency(long latency) {
    tLatencies.get().add(latency);
  }
}
