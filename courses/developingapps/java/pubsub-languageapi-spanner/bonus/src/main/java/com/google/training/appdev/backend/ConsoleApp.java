/*
 * Copyright 2018 Google Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.google.training.appdev.backend;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.cloud.pubsub.v1.AckReplyConsumer;
import com.google.cloud.pubsub.v1.MessageReceiver;
import com.google.cloud.pubsub.v1.Subscriber;
import com.google.cloud.pubsub.v1.SubscriptionAdminClient;
import com.google.common.util.concurrent.MoreExecutors;
import com.google.pubsub.v1.PubsubMessage;
import com.google.pubsub.v1.PushConfig;
import com.google.pubsub.v1.SubscriptionName;
import com.google.pubsub.v1.TopicName;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;


import com.google.training.appdev.services.gcp.domain.Feedback;
import com.google.training.appdev.services.gcp.languageapi.LanguageService;
import com.google.training.appdev.services.gcp.spanner.SpannerService;

public class ConsoleApp {

  public static void main(String... args) throws Exception {

    Logger logger = LoggerFactory.getLogger(ConsoleApp.class);
    String projectId = System.getenv("GCLOUD_PROJECT");
    System.out.println("Project: " + projectId);
    TopicName topic = TopicName.create(projectId, "feedback");

    LanguageService languageService = LanguageService.create();
    SpannerService spannerService = SpannerService.create();

    SubscriptionName subscription = SubscriptionName.create(projectId, "worker-subscription");
    System.out.println("Starting...");
    try (SubscriptionAdminClient subscriptionAdminClient = SubscriptionAdminClient.create()) {

      System.out.println("Creating subscription...");
      subscriptionAdminClient.createSubscription(subscription, topic, PushConfig.getDefaultInstance(), 0);
      System.out.println("Created.");
    }

    MessageReceiver receiver =
        new MessageReceiver() {
          @Override
          public void receiveMessage(PubsubMessage message, AckReplyConsumer consumer) {
            String fb = message.getData().toStringUtf8();
            consumer.ack();

            logger.info("\n\n**************\n\nId : " + message.getMessageId());
            logger.info("\n\n**************\n\nData : " + fb);
            consumer.ack();
            try {
                ObjectMapper mapper = new ObjectMapper();
                Feedback feedback = mapper.readValue(fb, Feedback.class);
                float sentimentScore = languageService.analyseSentiment(feedback.getFeedback());
                feedback.setSentimentScore(sentimentScore);
                spannerService.insertFeedback(feedback);
            } catch (Exception e) {
                logger.error("PubSub receiver failed: "+ e.getMessage());
                e.printStackTrace();
            }


          }
        };
        Subscriber subscriber = null;
        try {
            subscriber = Subscriber.defaultBuilder(subscription, receiver).build();
            subscriber.addListener(
                new Subscriber.Listener() {
                    @Override
                    public void failed(Subscriber.State from, Throwable failure) {
                    // Handle failure. This is called when the Subscriber encountered a fatal error and is shutting down.
                    System.err.println(failure);
                    }
                },
                MoreExecutors.directExecutor());
            subscriber.startAsync().awaitRunning();
            System.out.println("Started. Press any key to quit and remove subscription");

            System.in.read();

        } finally {
            if (subscriber != null) {
                subscriber.stopAsync().awaitTerminated();
            }
            try (SubscriptionAdminClient subscriptionAdminClient = SubscriptionAdminClient.create()) {

                System.out.println("Deleting subscription...");
                subscriptionAdminClient.deleteSubscription(subscription);
                System.out.println("Deleted.");
            }
        }
    }
}
