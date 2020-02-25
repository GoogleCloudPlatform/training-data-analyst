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

import com.beust.jcommander.JCommander;
import com.beust.jcommander.Parameter;
import com.google.api.gax.batching.FlowControlSettings;
import com.google.api.gax.core.FixedExecutorProvider;
import com.google.cloud.pubsub.v1.AckReplyConsumer;
import com.google.cloud.pubsub.v1.MessageReceiver;
import com.google.pubsub.v1.PubsubMessage;
import com.google.pubsub.v1.ProjectSubscriptionName;
import java.util.Map;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicLong;
import org.joda.time.DateTime;
import org.threeten.bp.Duration;

/** A basic Pub/Sub subscriber for purposes of demonstrating use of the API. */
public class Subscriber implements MessageReceiver {
  public static class Args {
    @Parameter(
      names = {"--project", "-p"},
      required = true,
      description = "The Google Cloud Pub/Sub project in which the subscription exists."
    )
    public String project = null;

    @Parameter(
      names = {"--subscription", "-s"},
      required = true,
      description = "The Google Cloud Pub/Sub subscription to which to subscribe."
    )
    public String subscription = null;
  }

  private static final String TOPIC = "pubsub-e2e-example";

  private final Args args;
  private com.google.cloud.pubsub.v1.Subscriber subscriber;
  private ScheduledExecutorService executor;

  private AtomicLong receivedMessageCount = new AtomicLong(0);
  private AtomicLong processedMessageCount = new AtomicLong(0);
  private AtomicLong lastReceivedTimestamp = new AtomicLong(0);

  private Subscriber(Args args) {
    this.args = args;

    this.executor = Executors.newScheduledThreadPool(1000);
    ProjectSubscriptionName subscription = ProjectSubscriptionName.of(args.project, args.subscription);
    com.google.cloud.pubsub.v1.Subscriber.Builder builder =
        com.google.cloud.pubsub.v1.Subscriber.newBuilder(subscription, this);
    try {
      this.subscriber = builder.build();
    } catch (Exception e) {
      System.out.println("Could not create subscriber: " + e);
      System.exit(1);
    }
  }

  @Override
  public void receiveMessage(PubsubMessage message, AckReplyConsumer consumer) {
    long receivedCount = receivedMessageCount.addAndGet(1);
    lastReceivedTimestamp.set(DateTime.now().getMillis());

    if (receivedCount % 100 == 0) {
      System.out.println("Received " + receivedCount + " messages.");
    }

    byte[] extraBytes = new byte[5000000];

    executor.schedule(() -> {
      long now = DateTime.now().getMillis();
      // This is here just to keep a hold on extraBytes so it isn't deallocated yet.
      extraBytes[0] = (byte)now;
      consumer.ack();
      long processedCount = processedMessageCount.addAndGet(1);
      if (processedCount % 100 == 0) {
        System.out.println("Processed " + processedCount + " messages.");
      }
      lastReceivedTimestamp.set(now);
    }, 30, TimeUnit.SECONDS);
  }

  private void run() {
    subscriber.startAsync();
    while (true) {
      long now = DateTime.now().getMillis();
      long lastReceived = lastReceivedTimestamp.get();
      if (lastReceived > 0 && ((now - lastReceived) > 60000)) {
        subscriber.stopAsync();
        break;
      }
      try {
        Thread.sleep(5000);
      } catch (InterruptedException e) {
        System.out.println("Error while waiting for completion: " + e);
      }
    }
    System.out.println(
        "Subscriber has not received message in 60s. Stopping.");
    subscriber.awaitTerminated();
  }

  public static void main(String[] args) {
    Args parsedArgs = new Args();
    JCommander.newBuilder().addObject(parsedArgs).build().parse(args);
    Subscriber s = new Subscriber(parsedArgs);
    s.run();
    System.exit(0);
  }
}
