/*
 * Copyright (C) 2016 Google Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not
 * use this file except in compliance with the License. You may obtain a copy of
 * the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations under
 * the License.
 */

package com.google.cloud.training.mlongcp;

import org.apache.beam.runners.dataflow.DataflowRunner;
import org.apache.beam.runners.dataflow.options.DataflowPipelineOptions;
import org.apache.beam.sdk.Pipeline;
import org.apache.beam.sdk.PipelineResult;
import org.apache.beam.sdk.options.Default;
import org.apache.beam.sdk.options.Description;
import org.apache.beam.sdk.options.PipelineOptionsFactory;
import org.apache.beam.sdk.transforms.windowing.FixedWindows;
import org.apache.beam.sdk.transforms.windowing.Window;
import org.apache.beam.sdk.values.PCollection;
import org.joda.time.Duration;

/**
 * Adds prediction to incoming information.
 * 
 * @author vlakshmanan
 *
 */
public class AddPrediction {
  // private static final Logger LOG = LoggerFactory.getLogger(AddPrediction.class);

  public static interface MyOptions extends DataflowPipelineOptions {
    @Description("Output dir or bqdataset.table")
    @Default.String("../output/")
    String getOutput();

    void setOutput(String s);

    
    @Description("Input file or pubsub-topic")
    @Default.String("../exampledata.csv.gz")
    String getInput();

    void setInput(String s);
    
    
    @Description("If real-time, it will read incoming flight info from Pub/Sub")
    @Default.Boolean(false)
    boolean isRealtime();
    void setRealtime(boolean r);
  }

  public static void main(String[] args) {
    MyOptions options = PipelineOptionsFactory.fromArgs(args).withValidation().as(MyOptions.class);
    if (options.isRealtime()) {
      options.setStreaming(true);
      options.setRunner(DataflowRunner.class);
    }    
    
   
    Pipeline p = Pipeline.create(options);

    InputOutput io;
    if (options.isRealtime()) {
      // in real-time, we read from PubSub and write to BigQuery
      io = new PubSubBigQuery();
    } else {
      io = new TextInputOutput();
    } 
    
    PCollection<Baby> babies = io //
        .readInstances(p, options) //
        .apply(Window.<Baby> into(FixedWindows.of(Duration.standardSeconds(20))).withAllowedLateness(Duration.standardSeconds(10)).discardingFiredPanes());

    io.writePredictions(babies, options);

    PipelineResult result = p.run();
    if (!options.isRealtime()) {
      result.waitUntilFinish();
    }
  }
}
