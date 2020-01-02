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
package com.google.training.appdev.services.gcp.pubsub;

import com.fasterxml.jackson.databind.ObjectMapper;

import com.google.cloud.ServiceOptions;
import com.google.api.core.ApiFuture;
import com.google.cloud.pubsub.v1.Publisher;
import com.google.protobuf.ByteString;
import com.google.pubsub.v1.PubsubMessage;
import com.google.pubsub.v1.TopicName;

import java.util.List;

import com.google.training.appdev.services.gcp.domain.Answer;
import com.google.training.appdev.services.gcp.domain.Feedback;

import org.springframework.stereotype.Service;


@Service
public class PublishService {
    private static final String PROJECT_ID = ServiceOptions.getDefaultProjectId();
    private static final String FEEDBACK_TOPIC_NAME = "feedback";
    public static final String ANSWER_TOPIC_NAME = "answers";

    public void publishFeedback(Feedback feedback) throws Exception {
        ObjectMapper mapper = new ObjectMapper();
        String feedbackMessage = mapper.writeValueAsString(feedback);
        publishMessage(feedbackMessage, FEEDBACK_TOPIC_NAME);
    }

    public void publishAnswers(List<Answer> answers, String quiz) throws Exception {
        for(Answer answer : answers){
            answer.setQuiz(quiz);
            ObjectMapper mapper = new ObjectMapper();
            String feedbackMessage = mapper.writeValueAsString(answer);
            publishMessage(feedbackMessage, ANSWER_TOPIC_NAME);
        }
    }

    private void publishMessage(String feedbackMessage, String topic) throws Exception {
        TopicName topicName = TopicName.create(PROJECT_ID, topic);
        Publisher publisher = null;
        ApiFuture<String> messageIdFuture = null;
        try {

            publisher = Publisher.defaultBuilder(topicName).build();

            ByteString data = ByteString.copyFromUtf8(feedbackMessage);
            PubsubMessage pubsubMessage = PubsubMessage.newBuilder().setData(data).build();

            messageIdFuture = publisher.publish(pubsubMessage);

        } finally {

            String messageId = messageIdFuture.get();

            System.out.println("published with message ID: " + messageId);

            if (publisher != null) {
                // When finished with the publisher, shutdown to free up resources.
                publisher.shutdown();
            }
        }
    }
}
