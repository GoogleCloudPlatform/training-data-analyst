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
import com.google.api.core.ApiFuture;
import com.google.api.gax.batching.BatchingSettings;
import com.google.api.gax.core.FixedExecutorProvider;
import com.google.cloud.sme.Entities;
import com.google.cloud.sme.common.ActionReader;
import com.google.cloud.sme.common.ActionUtils;
import com.google.cloud.sme.common.FileActionReader;
import com.google.pubsub.v1.PubsubMessage;
import com.google.pubsub.v1.ProjectTopicName;
import java.util.concurrent.Executors;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.atomic.AtomicLong;
import org.joda.time.DateTime;
import org.threeten.bp.Duration;

/** A basic Pub/Sub publisher for purposes of demonstrating use of the API. */
public class Publisher {
  public static class Args {
    @Parameter(
      names = {"--project", "-p"},
      required = true,
      description = "The Google Cloud Pub/Sub project in which the topic exists."
    )
    public String project = null;
  }

  private static final String SOURCE_DATA = "actions.csv";
  private static final String TIMESTAMP_KEY = "publish_time";
  private static final String TOPIC = "pubsub-e2e-example";
  private static final int MESSAGE_COUNT = 1000;

  private final Args args;
  private com.google.cloud.pubsub.v1.Publisher publisher;
  private ActionReader actionReader;
  private AtomicLong awaitedFutures;
  private ExecutorService executor = Executors.newCachedThreadPool();

  private Publisher(Args args, ActionReader actionReader) {
    this.args = args;
    this.actionReader = actionReader;
    this.awaitedFutures = new AtomicLong();

    ProjectTopicName topic = ProjectTopicName.of(args.project, TOPIC);
    com.google.cloud.pubsub.v1.Publisher.Builder builder =
        com.google.cloud.pubsub.v1.Publisher.newBuilder(topic);
    try {
      this.publisher = builder.build();
    } catch (Exception e) {
      System.out.println("Could not create publisher: " + e);
      System.exit(1);
    }
  }

  private void Publish(Entities.Action publishAction) {
    awaitedFutures.incrementAndGet();
    final long publishTime = DateTime.now().getMillis();
    PubsubMessage message =
        PubsubMessage.newBuilder()
            .setData(ActionUtils.encodeAction(publishAction))
            .putAttributes(TIMESTAMP_KEY, Long.toString(publishTime))
            .build();
    ApiFuture<String> response = publisher.publish(message);
    response.addListener(
        () -> {
          try {
            response.get();
          } catch (Exception e) {
            System.out.println("Could not publish a message: " + e);
          } finally {
            awaitedFutures.decrementAndGet();
          }
        },
        executor);
  }

  private void run() {
    awaitedFutures.incrementAndGet();

    long count = 0;
    Entities.Action nextAction = actionReader.next();
    for (int i = 0; i < MESSAGE_COUNT; ++i) {
      Publish(nextAction);
      nextAction = actionReader.next();
    }
    awaitedFutures.decrementAndGet();
  }

  private void waitForPublishes() {
    try {
      while (awaitedFutures.longValue() > 0) {
        Thread.sleep(5000);
      }
    } catch (InterruptedException e) {
      System.out.println("Error while waiting for completion: " + e);
    }
    executor.shutdownNow();
  }

  private void shutdown() {
    try {
      publisher.shutdown();
    } catch (Exception e) {
      System.out.println("Error while shutting down: " + e);
    }
  }

  public static void main(String[] args) {
    Args parsedArgs = new Args();
    JCommander.newBuilder().addObject(parsedArgs).build().parse(args);

    ActionReader actionReader = new FileActionReader(SOURCE_DATA);

    Publisher p = new Publisher(parsedArgs, actionReader);

    p.run();
    p.waitForPublishes();
    p.shutdown();
    System.exit(0);
  }
}
