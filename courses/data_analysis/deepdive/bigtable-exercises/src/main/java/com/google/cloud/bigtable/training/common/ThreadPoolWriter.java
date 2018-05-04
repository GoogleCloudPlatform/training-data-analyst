package com.google.cloud.bigtable.training.common;

import java.util.Date;
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
      System.out.println("Inserted row " + c + " at timestamp " + new Date(timestamp));
    }
  }

  public void shutdownAndWait() throws InterruptedException {
    executor.shutdown();
    executor.awaitTermination(5, TimeUnit.MINUTES);
  }
}
