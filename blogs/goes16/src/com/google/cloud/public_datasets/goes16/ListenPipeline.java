/*
 * Copyright (C) 2017 Google Inc.
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
package com.google.cloud.public_datasets.goes16;

import org.apache.beam.runners.dataflow.options.DataflowPipelineOptions;
import org.apache.beam.sdk.Pipeline;
import org.apache.beam.sdk.io.gcp.pubsub.PubsubIO;
import org.apache.beam.sdk.options.Default;
import org.apache.beam.sdk.options.Description;
import org.apache.beam.sdk.options.PipelineOptionsFactory;
import org.apache.beam.sdk.transforms.DoFn;
import org.apache.beam.sdk.transforms.ParDo;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;


/**
 * Scales out the APDetector to a large number of volume scans
 * 
 * @author vlakshmanan
 *
 */
public class ListenPipeline {
  private static final Logger log = LoggerFactory.getLogger(ListenPipeline.class);

  public static interface MyOptions extends DataflowPipelineOptions {
    @Description("Output directory")
    @Default.String("gs://cloud-training-demos-ml/goes16/")
    String getOutput();

    void setOutput(String s);
  }

  @SuppressWarnings("serial")
  public static void main(String[] args) {
    MyOptions options = PipelineOptionsFactory.fromArgs(args).withValidation().as(MyOptions.class);
    options.setTempLocation(options.getOutput() + "staging");
    Pipeline p = Pipeline.create(options);

    String topic = "projects/gcp-public-data---goes-16/topics/gcp-public-data-goes-16";
    
    // listen to topic
    p//
      .apply("ReadMessage", PubsubIO.readStrings().fromTopic(topic)) //
      .apply("ParseMessage", ParDo.of(new DoFn<String, String>() {
        @ProcessElement
        public void processElement(ProcessContext c) throws Exception {
          String message = c.element();
          String[] fields = message.split(" ");
          for (String f : fields) {
            if (f.startsWith("objectId=")) {
              String objectId = f.replace("objectId=", "");
              c.output("gs://gcp-public-data-goes-16/" + objectId);
            }
          }
        }
      })) //
      .apply("ProcessFile", ParDo.of(new DoFn<String, String>() {
        @ProcessElement
        public void processElement(ProcessContext c) throws Exception {
          String gcsFileName = c.element();
          log.info("Processing " + gcsFileName);
        }
      }));

    
    p.run();
  }
}
