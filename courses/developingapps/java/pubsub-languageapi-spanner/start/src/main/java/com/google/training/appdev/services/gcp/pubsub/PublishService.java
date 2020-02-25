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
import com.google.api.core.ApiFutures;
import com.google.cloud.pubsub.v1.Publisher;
import com.google.cloud.pubsub.v1.TopicAdminClient;
import com.google.protobuf.ByteString;
import com.google.pubsub.v1.PubsubMessage;
import com.google.pubsub.v1.TopicName;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import com.google.training.appdev.services.gcp.domain.Feedback;

import org.springframework.stereotype.Service;

import java.io.IOException;


@Service
public class PublishService {
    // TODO: Declare and initialize two Strings, PROJECT_ID and TOPIC_NAME

    

    // END TODO

    public void publishFeedback(Feedback feedback) throws Exception {
        // Generate a serialized JSON representation of the feedback object
        ObjectMapper mapper = new ObjectMapper();
        String feedbackMessage = mapper.writeValueAsString(feedback);

        // TODO: Create a TopicName object for the feedback topic in the project

        

        // END TODO

        // TODO: Declare a publisher for the topic
        
        

        // END TODO

        // messageIdFuture will contain the MessageId when the Pub/Sub publish returns
        ApiFuture<String> messageIdFuture = null;

        try {

            // TODO: Initialize the publisher using a builder and the topicName

            

            // END TODO
            
            // TODO: Copy the serialized message to a byte string

            

            // END TODO

            // TODO: Create a Pub/Sub message using a builder; set the message data

            

            // END TODO

            // TODO: Publish the message, assign to the messageIdFuture

            

            // END TODO
        
        } finally {

            // TODO: Get the messageId from the messageIdFuture

            String messageId = "Replace string with: messageIdFuture.get();";

            // END TODO

            System.out.println("published with message ID: " + messageId);

            // TODO: Shutdown the publisher to free up resources

            
            

            // END TODO
        }

        
    }

}
