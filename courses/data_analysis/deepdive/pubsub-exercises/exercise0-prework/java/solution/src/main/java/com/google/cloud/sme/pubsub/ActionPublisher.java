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

import com.google.api.core.ApiFuture;
import com.google.api.core.ApiFutureCallback;
import com.google.api.core.ApiFutures;
import com.google.api.gax.rpc.ApiException;
import com.google.cloud.pubsub.v1.Publisher;
import com.google.cloud.sme.common.ActionUtils;
import com.google.cloud.sme.Entities;
import com.google.pubsub.v1.PubsubMessage;
import com.google.pubsub.v1.ProjectTopicName;

/** A basic Pub/Sub publisher for purposes of demonstrating use of the API. */
public class ActionPublisher {
  private Publisher publisher = null;

  public ActionPublisher(String project, String topic) {
    ProjectTopicName fullTopic = ProjectTopicName.of(project, topic);
    Publisher.Builder builder = Publisher.newBuilder(fullTopic);
    try {
      this.publisher = builder.build();
    } catch (Exception e) {
      System.out.println("Could not create publisher: " + e);
    }
  }

  public void publish(Entities.Action action) {
    PubsubMessage message =
        PubsubMessage.newBuilder()
            .setData(ActionUtils.encodeActionAsJson(action))
            .build();
    ApiFuture<String> response = publisher.publish(message);
    ApiFutures.addCallback(response, new ApiFutureCallback<String>() {

      @Override
      public void onFailure(Throwable throwable) {
        if (throwable instanceof ApiException) {
          ApiException apiException = ((ApiException) throwable);
          // details on the API exception
          System.out.println(apiException.getStatusCode().getCode());
          System.out.println(apiException.isRetryable());
        }
        System.out.println("Error publishing message : " + message);
      }

      @Override
      public void onSuccess(String messageId) {
      }
    });
  }
}
