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

/** A basic Pub/Sub subscriber for purposes of demonstrating use of the API. */
public class ActionSubscriber {

  /** Creates a new subscriber associated with the given project and subscription. */
  public ActionSubscriber(String project, String subscription) {
  }

  /** Returns the number of VIEW action seen */
  public long getViewCount() {
    return -1;
  }

  /** Returns true if action is a VIEW action. */
  private boolean isViewAction(Entities.Action action) {
    return action.getAction() == Entities.Action.ActionType.VIEW;
  }
}
