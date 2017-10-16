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
package com.google.cloud.training.quests.iotlab;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;

import org.apache.beam.runners.dataflow.options.DataflowPipelineOptions;
import org.apache.beam.sdk.Pipeline;
import org.apache.beam.sdk.io.gcp.bigquery.BigQueryIO;
import org.apache.beam.sdk.io.gcp.pubsub.PubsubIO;
import org.apache.beam.sdk.options.PipelineOptionsFactory;
import org.apache.beam.sdk.transforms.DoFn;
import org.apache.beam.sdk.transforms.Max;
import org.apache.beam.sdk.transforms.ParDo;
import org.apache.beam.sdk.transforms.windowing.SlidingWindows;
import org.apache.beam.sdk.transforms.windowing.Window;
import org.apache.beam.sdk.values.KV;
import org.joda.time.Duration;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.google.api.services.bigquery.model.TableFieldSchema;
import com.google.api.services.bigquery.model.TableRow;
import com.google.api.services.bigquery.model.TableSchema;

/**
 * A dataflow pipeline that listens to a PubSub topic and writes out aggregates
 * on windows to BigQuery
 * 
 * @author vlakshmanan
 *
 */
public class Main {
  private static final Logger LOG = LoggerFactory.getLogger(Main.class);

  public static interface MyOptions extends DataflowPipelineOptions {

  }

  @SuppressWarnings("serial")
  public static void main(String[] args) {
    MyOptions options = PipelineOptionsFactory.fromArgs(args).withValidation().as(MyOptions.class);
    options.setStreaming(true);
    Pipeline p = Pipeline.create(options);

    String topic = "projects/" + options.getProject() + "/topics/iotlab";
    String output = options.getProject() + ":" + "iotlab.sensordata";

    LOG.info("Reading from " + topic);
    LOG.info("Writing to " + output);
    
    // Build the table schema for the output table.
    List<TableFieldSchema> fields = new ArrayList<>();
    fields.add(new TableFieldSchema().setName("timestamp").setType("TIMESTAMP"));
    fields.add(new TableFieldSchema().setName("device").setType("INTEGER"));
    fields.add(new TableFieldSchema().setName("temperature").setType("FLOAT64"));
    TableSchema schema = new TableSchema().setFields(fields);

    p //
        .apply("GetMessages", PubsubIO.readStrings().fromTopic(topic)) //
        .apply("ParseMessage", ParDo.of(new DoFn<String, KV<Integer,Double>>() {
          @ProcessElement
          public void processElement(ProcessContext c) throws Exception {
            String line = c.element();
            // iotlab-registry/device-1-payload-90
            String[] pieces = line.split("-");
            int device = Integer.parseInt(pieces[1]);
            double temperature = Double.parseDouble(pieces[3]);
            c.output(KV.of(device, temperature));
          }
        })) //
        .apply("window",
            Window.into(SlidingWindows//
                .of(Duration.standardMinutes(1))//
                .every(Duration.standardSeconds(30)))) //
    
    
        .apply("MaxTemperature", Max.doublesPerKey()) //
        .apply("ToBQRow", ParDo.of(new DoFn<KV<Integer,Double>, TableRow>() {
          @ProcessElement
          public void processElement(ProcessContext c) throws Exception {
            TableRow row = new TableRow();
            row.set("timestamp", Instant.now().toString());
            row.set("device", c.element().getKey());
            row.set("max_temp", c.element().getValue());
            c.output(row);
          }
        })) //
        .apply(BigQueryIO.writeTableRows().to(output)//
            .withSchema(schema)//
            .withWriteDisposition(BigQueryIO.Write.WriteDisposition.WRITE_APPEND)
            .withCreateDisposition(BigQueryIO.Write.CreateDisposition.CREATE_IF_NEEDED));

    p.run();
  }
}
