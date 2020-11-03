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
import com.google.cloud.pubsub.v1.AckReplyConsumer;
import com.google.cloud.pubsub.v1.MessageReceiver;
import com.google.cloud.sme.Entities;
import com.google.cloud.sme.common.ActionUtils;
import com.google.pubsub.v1.ProjectSubscriptionName;
import com.google.pubsub.v1.PubsubMessage;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;
import org.joda.time.DateTime;

/** A basic Pub/Sub subscriber for purposes of demonstrating use of the API. */
public class Subscriber implements MessageReceiver {
  public static class Args {
    @Parameter(
        names = {"--project", "-p"},
        required = true,
        description = "The Google Cloud Pub/Sub project in which the subscription exists.")
    public String project = null;

    @Parameter(
        names = {"--subscription", "-s"},
        required = true,
        description = "The Google Cloud Pub/Sub subscription name to which to subscribe.")
    public String subscription = null;

    @Parameter(
        names = {"--ordered", "-o"},
        required = false,
        description = "Whether or not to publish messages with an ordering key.")
    public Boolean ordered = false;
  }

  private static final String SEQUENCE_NUM_KEY = "sequence_num";

  private final Args args;
  private com.google.cloud.pubsub.v1.Subscriber subscriber;

  private AtomicLong receivedMessageCount = new AtomicLong(0);
  private AtomicLong outOfOrderCount = new AtomicLong(0);
  private AtomicLong lastReceivedTimestamp = new AtomicLong(0);
  private ConcurrentHashMap<Long, Long> largestSequenceNumPerUser =
      new ConcurrentHashMap<Long, Long>();
  private ConcurrentHashMap<Long, Long> seenSequenceNums = new ConcurrentHashMap<Long, Long>();

  private Subscriber(Args args) {
    this.args = args;

    ProjectSubscriptionName subscription =
        ProjectSubscriptionName.of(args.project, args.subscription);
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
    Entities.Action action = ActionUtils.decodeAction(message.getData());
    long size = message.getData().size();
    long now = DateTime.now().getMillis();
    long receivedCount = receivedMessageCount.addAndGet(1);
    long sequenceNum = Long.parseLong(message.getAttributesOrDefault(SEQUENCE_NUM_KEY, "-1"));
    if (seenSequenceNums.putIfAbsent(sequenceNum, sequenceNum) != null) {
      consumer.ack();
      return;
    }

    lastReceivedTimestamp.set(now);
    long largestSequeceNum =
        largestSequenceNumPerUser.compute(
            action.getUserId(), (k, v) -> v == null ? sequenceNum : Math.max(v, sequenceNum));
    if (largestSequeceNum > sequenceNum) {
      outOfOrderCount.incrementAndGet();
    }

    if (receivedCount % 100000 == 0) {
      System.out.println(
          "Received "
              + receivedCount
              + " messages, "
              + outOfOrderCount.get()
              + " were out of order.");
    }
    consumer.ack();
  }

  private void run() {
    subscriber.startAsync();
    while (true) {
      long now = DateTime.now().getMillis();
      long currentReceived = lastReceivedTimestamp.get();
      if (currentReceived > 0 && ((now - currentReceived) > 30000)) {
        subscriber.stopAsync();
        break;
      }
      try {
        Thread.sleep(5000);
      } catch (InterruptedException e) {
        System.out.println("Error while waiting for completion: " + e);
      }
    }
    System.out.println("Subscriber has not received message in 30s. Stopping.");
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
