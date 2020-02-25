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
import com.google.cloud.sme.Entities;
import com.google.cloud.sme.common.ActionReader;
import com.google.cloud.sme.common.ActionUtils;
import com.google.cloud.sme.common.FileActionReader;

/** A basic Pub/Sub example for demonstrating use of the API. */
public class Example {
  public static class Args {
    @Parameter(
      names = {"--input", "-i"},
      description = "The file from which to grab the events to publish."
    )
    public String inputFile = null;

    @Parameter(
      names = {"--project", "-p"},
      required = true,
      description = "The Google Cloud Pub/Sub project in which the topic exists."
    )
    public String project = null;

    @Parameter(
      names = {"--topic", "-t"},
      description = "The Google Cloud Pub/Sub topic name to which to publish."
    )
    public String topic = null;

    @Parameter(
      names = {"--subscription", "-s"},
      description =
          "The Google Cloud Pub/Sub subscriber name on which to subscribe."
    )
    public String subscription = null;
  }

  public static void main(String[] args) {
    Args parsedArgs = new Args();
    JCommander.newBuilder().addObject(parsedArgs).build().parse(args);

    ActionSubscriber subscriber = null;
    if (parsedArgs.subscription != null) {
      subscriber = new ActionSubscriber(parsedArgs.project, parsedArgs.subscription);
    }

    if (parsedArgs.topic != null && parsedArgs.inputFile != null) {
      ActionReader actionReader = new FileActionReader(parsedArgs.inputFile);
      ActionPublisher publisher = new ActionPublisher(parsedArgs.project, parsedArgs.topic);
      Entities.Action nextAction = actionReader.next();
      while (nextAction != null) {
        publisher.publish(nextAction);
        nextAction = actionReader.next();
      }
    }

    try {
      Thread.sleep(10000);
    } catch (Exception e) {
    }

    System.out.println("View action count: " + subscriber.getViewCount());
    System.exit(0);
  }
}
