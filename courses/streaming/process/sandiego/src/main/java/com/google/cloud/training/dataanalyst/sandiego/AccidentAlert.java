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

package com.google.cloud.training.dataanalyst.sandiego;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import org.apache.beam.runners.dataflow.options.DataflowPipelineOptions;
import org.apache.beam.sdk.Pipeline;
import org.apache.beam.sdk.io.gcp.pubsub.PubsubIO;
import org.apache.beam.sdk.io.gcp.bigquery.BigQueryIO;
import org.apache.beam.sdk.options.Default;
import org.apache.beam.sdk.options.Description;
import org.apache.beam.sdk.options.PipelineOptionsFactory;
import org.apache.beam.sdk.transforms.DoFn;
import org.apache.beam.sdk.transforms.Mean;
import org.apache.beam.sdk.transforms.ParDo;
import org.apache.beam.sdk.transforms.View;
import org.apache.beam.sdk.transforms.windowing.SlidingWindows;
import org.apache.beam.sdk.transforms.windowing.Window;
import org.apache.beam.sdk.values.KV;
import org.apache.beam.sdk.values.PCollection;
import org.apache.beam.sdk.values.PCollectionView;
import org.joda.time.Duration;

import com.google.api.services.bigquery.model.TableFieldSchema;
import com.google.api.services.bigquery.model.TableRow;
import com.google.api.services.bigquery.model.TableSchema;

/**
 * A dataflow pipeline that finds lanes in which traffic is much slower than in
 * adjacent lanes.
 * 
 * @author vlakshmanan
 *
 */
public class AccidentAlert {

  public static interface MyOptions extends DataflowPipelineOptions {
    @Description("Over how long a time period should we average? (in minutes)")
    @Default.Double(60.0)
    Double getAveragingInterval();

    void setAveragingInterval(Double d);

    @Description("Simulation speedup factor. Use 1.0 if no speedup")
    @Default.Double(60.0)
    Double getSpeedupFactor();

    void setSpeedupFactor(Double d);

    @Description("If speed in lane is x of the average speed, then accident in lane. What is x?")
    @Default.Double(0.5)
    Double getRatioThreshold();

    void setRatioThreshold(Double d);

    @Description("Also stream to Bigtable?")
    @Default.Boolean(false)
    boolean getBigtable();

    void setBigtable(boolean b);
  }

  @SuppressWarnings("serial")
  public static void main(String[] args) {
    MyOptions options = PipelineOptionsFactory.fromArgs(args).withValidation().as(MyOptions.class);
    options.setStreaming(true);
    Pipeline p = Pipeline.create(options);

    String topic = "projects/" + options.getProject() + "/topics/sandiego";
    String accidentsTable = options.getProject() + ":demos.accidents";
    double RATIO = options.getRatioThreshold();

    // if we need to average over 60 minutes and speedup is 30x
    // then we need to average over 2 minutes of sped-up stream
    Duration averagingInterval = Duration
        .millis(Math.round(1000 * 60 * (options.getAveragingInterval() / options.getSpeedupFactor())));
    Duration averagingFrequency = averagingInterval.dividedBy(2); // 2 times
    // in
    // window
    System.out.println("Averaging interval = " + averagingInterval);
    System.out.println("Averaging freq = " + averagingFrequency);

    // Build the table schema for the output table.
    List<TableFieldSchema> fields = new ArrayList<>();
    fields.add(new TableFieldSchema().setName("timestamp").setType("TIMESTAMP"));
    fields.add(new TableFieldSchema().setName("latitude").setType("FLOAT"));
    fields.add(new TableFieldSchema().setName("longitude").setType("FLOAT"));
    fields.add(new TableFieldSchema().setName("highway").setType("STRING"));
    fields.add(new TableFieldSchema().setName("direction").setType("STRING"));
    fields.add(new TableFieldSchema().setName("lane").setType("INTEGER"));
    fields.add(new TableFieldSchema().setName("speed").setType("FLOAT"));
    fields.add(new TableFieldSchema().setName("sensorId").setType("STRING"));
    TableSchema schema = new TableSchema().setFields(fields);

    PCollection<LaneInfo> currentConditions = p //
        .apply("GetMessages", PubsubIO.readStrings().fromTopic(topic)) //
        .apply("ExtractData", ParDo.of(new DoFn<String, LaneInfo>() {
          @ProcessElement
          public void processElement(ProcessContext c) throws Exception {
            String line = c.element();
            c.output(LaneInfo.newLaneInfo(line));
          }
        }));

    if (options.getBigtable()) {
      BigtableHelper.writeToBigtable(currentConditions, options);
    }

    PCollection<LaneInfo> laneInfo = currentConditions //
        .apply("TimeWindow",
            Window.into(SlidingWindows//
                .of(averagingInterval)//
                .every(averagingFrequency)));

    PCollectionView<Map<String, Double>> avgSpeedLocation = laneInfo //
        .apply("ByLocation", ParDo.of(new DoFn<LaneInfo, KV<String, Double>>() {
          @ProcessElement
          public void processElement(ProcessContext c) throws Exception {
            LaneInfo info = c.element();
            String key = info.getLocationKey();
            Double speed = info.getSpeed();
            c.output(KV.of(key, speed));
          }
        })) //
        .apply("AvgByLocation", Mean.perKey()) //
        .apply("ToView", View.asMap());

    PCollection<LaneInfo> accidents = laneInfo.apply("FindSlowdowns", ParDo.of(new DoFn<LaneInfo, LaneInfo>() {
      @ProcessElement
      public void processElement(ProcessContext c) throws Exception {
        LaneInfo info = c.element();
        String location = info.getLocationKey();
        double speed = info.getSpeed();
        double avgSpeed = c.sideInput(avgSpeedLocation).get(location);
        if (speed < RATIO * avgSpeed) {
          // 50% of average speed?
          c.output(info);
        }
      }
    }).withSideInputs(avgSpeedLocation)); //

    accidents.apply("ToBQRow", ParDo.of(new DoFn<LaneInfo, TableRow>() {
      @ProcessElement
      public void processElement(ProcessContext c) throws Exception {
        TableRow row = new TableRow();
        LaneInfo info = c.element();
        row.set("timestamp", info.getTimestamp());
        row.set("latitude", info.getLatitude());
        row.set("longitude", info.getLongitude());
        row.set("highway", info.getHighway());
        row.set("direction", info.getDirection());
        row.set("lane", info.getLane());
        row.set("speed", info.getSpeed());
        row.set("sensorId", info.getSensorKey());
        c.output(row);
      }
    })) //
        .apply(BigQueryIO.writeTableRows().to(accidentsTable)//
            .withSchema(schema)//
            .withWriteDisposition(BigQueryIO.Write.WriteDisposition.WRITE_APPEND)
            .withCreateDisposition(BigQueryIO.Write.CreateDisposition.CREATE_IF_NEEDED));

    p.run();
  }
}
