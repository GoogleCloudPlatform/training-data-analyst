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

import com.google.cloud.pubsub.v1.AckReplyConsumer;
import com.google.cloud.pubsub.v1.MessageReceiver;
import com.google.cloud.pubsub.v1.Subscriber;
import com.google.cloud.sme.common.ActionUtils;
import com.google.cloud.sme.Entities;
import com.google.pubsub.v1.PubsubMessage;
import com.google.pubsub.v1.ProjectSubscriptionName;
import java.util.concurrent.ConcurrentHashMap;

/** A basic Pub/Sub subscriber for purposes of demonstrating use of the API. */
public class ActionSubscriber implements MessageReceiver {
  private com.google.cloud.pubsub.v1.Subscriber subscriber = null;
  private ConcurrentHashMap<String, Boolean> seenIds = new ConcurrentHashMap<String, Boolean>();

  public ActionSubscriber(String project, String subscription) {
    ProjectSubscriptionName fullSubscription =
        ProjectSubscriptionName.of(project, subscription);
    Subscriber.Builder builder = Subscriber.newBuilder(fullSubscription, this);
    try {
      this.subscriber = builder.build();
      this.subscriber.startAsync();
    } catch (Exception e) {
      System.out.println("Could not create and start subscriber: " + e);
    }
  }

  /** Returns the number of VIEW action seen */
  public long getViewCount() {
    return seenIds.size();
  }

  @Override
  public void receiveMessage(PubsubMessage message, AckReplyConsumer consumer) {
    Entities.Action action = ActionUtils.decodeActionFromJson(message.getData());
    if (isViewAction(action)) {
      seenIds.putIfAbsent(message.getMessageId(), true);
    }
    consumer.ack();
  }

  /** Returns true if action is a VIEW action. */
  private boolean isViewAction(Entities.Action action) {
    return action.getAction() == Entities.Action.ActionType.VIEW;
  }
}
