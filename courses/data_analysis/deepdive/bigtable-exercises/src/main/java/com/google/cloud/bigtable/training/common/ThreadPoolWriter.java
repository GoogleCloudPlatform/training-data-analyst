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

import java.util.Date;
import java.util.Map;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.RejectedExecutionHandler;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Helper class to write data to Bigtable.
 */
public class ThreadPoolWriter {
  private ThreadPoolExecutor executor;
  private AtomicInteger count = new AtomicInteger();

  public ThreadPoolWriter(int numThreads) {
    BlockingQueue q = new ArrayBlockingQueue(1000);
    RejectedExecutionHandler re = new ThreadPoolExecutor.CallerRunsPolicy();
    executor = new ThreadPoolExecutor(numThreads, numThreads,
        1, TimeUnit.MINUTES, q, re);
  }

  public void execute(Runnable r, long timestamp) {
    executor.execute(r);
    int c = count.incrementAndGet();
    if (c % 1000 == 0) {
      System.out.println("Inserted row " + c + " at " + new Date());
    }
  }

  /** helper function that adds error handling and parsing */
  public interface RunnableThatThrows {
    void run() throws java.io.IOException;
  }
  public void execute(RunnableThatThrows r, Map<String, String> point) {
    this.execute(() -> {
      try {
        r.run();
      } catch (java.io.IOException e) {
	e.printStackTrace();
      }
    }, Long.parseLong(point.get("time").toString()));
  }

  public void shutdownAndWait() throws InterruptedException {
    executor.shutdown();
    executor.awaitTermination(5, TimeUnit.MINUTES);
  }
}
