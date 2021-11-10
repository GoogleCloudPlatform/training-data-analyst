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

package com.google.cloud.training.flights;

import java.util.Map;

import org.apache.beam.runners.dataflow.DataflowRunner;
import org.apache.beam.runners.dataflow.options.DataflowPipelineOptions;
import org.apache.beam.sdk.Pipeline;
import org.apache.beam.sdk.PipelineResult;
import org.apache.beam.sdk.io.TextIO;
import org.apache.beam.sdk.options.Default;
import org.apache.beam.sdk.options.Description;
import org.apache.beam.sdk.options.PipelineOptionsFactory;
import org.apache.beam.sdk.transforms.DoFn;
import org.apache.beam.sdk.transforms.ParDo;
import org.apache.beam.sdk.transforms.View;
import org.apache.beam.sdk.transforms.windowing.SlidingWindows;
import org.apache.beam.sdk.transforms.windowing.Window;
import org.apache.beam.sdk.values.KV;
import org.apache.beam.sdk.values.PCollection;
import org.apache.beam.sdk.values.PCollectionView;
import org.joda.time.Duration;

/**
 * Adds prediction to incoming flight information.
 * 
 * @author vlakshmanan
 *
 */
@SuppressWarnings("serial")
public class AddRealtimePrediction {
  // private static final Logger LOG = LoggerFactory.getLogger(AddRealtimePrediction.class);

  public static interface MyOptions extends DataflowPipelineOptions {
    @Description("Bucket name")
    @Default.String("cloud-training-demos-ml")
    String getBucket();
    
    void setBucket(String s);
    
    @Description("If real-time, it will read incoming flight info from Pub/Sub")
    @Default.Boolean(false)
    boolean isRealtime();
    void setRealtime(boolean r);
    
    @Description("Simulation speedup factor if applicable")
    @Default.Long(1)
    long getSpeedupFactor();

    void setSpeedupFactor(long d);
    
    @Description("Where should we store the output (if realtime) -- bigquery or bigtable")
    @Default.Boolean(false)
    boolean isBigtable();
    void setBigtable(boolean r);
  }
  
  private static String getDelayPath(MyOptions opts) {
    return "gs://BUCKET/flights/chapter8/output/delays.csv".replace("BUCKET", opts.getBucket());
  }
  
  private static String getTempLocation(MyOptions opts) {
    return "gs://BUCKET/flights/staging".replace("BUCKET", opts.getBucket());
  }

  static PCollectionView<Map<String, Double>> readAverageDepartureDelay(Pipeline p, String path) {
    return p.apply("Read delays.csv", TextIO.read().from(path)) //
        .apply("Parse delays.csv", ParDo.of(new DoFn<String, KV<String, Double>>() {
          @ProcessElement
          public void processElement(ProcessContext c) throws Exception {
            String line = c.element();
            String[] fields = line.split(",");
            c.output(KV.of(fields[0], Double.parseDouble(fields[1])));
          }
        })) //
        .apply("toView", View.asMap());
  }
  
  public static void main(String[] args) {
    MyOptions options = PipelineOptionsFactory.fromArgs(args).withValidation().as(MyOptions.class);
    if (options.isRealtime()) {
      options.setStreaming(true);
    }    
    options.setRunner(DataflowRunner.class);
    options.setTempLocation(getTempLocation(options));
    Pipeline p = Pipeline.create(options);

    // in real-time, we read from PubSub and write to BigQuery
    InputOutput io;
    Duration averagingInterval = CreateTrainingDataset.AVERAGING_INTERVAL;
    Duration averagingFrequency = CreateTrainingDataset.AVERAGING_FREQUENCY;
    if (options.isRealtime()) {
      io = options.isBigtable()? new PubSubBigtable() : new PubSubBigQuery();
      
      // If we need to average over 60 minutes and speedup is 30x,
      // then we need to average over 2 minutes of sped-up stream
      averagingInterval = averagingInterval.dividedBy(options.getSpeedupFactor());
      averagingFrequency = averagingFrequency.dividedBy(options.getSpeedupFactor());
    } else {
      io = new BatchInputOutput();
    } 
    
    PCollection<Flight> allFlights = io.readFlights(p, options);

    PCollectionView<Map<String, Double>> avgDepDelay = readAverageDepartureDelay(p, getDelayPath(options));

    PCollection<Flight> hourlyFlights = allFlights.apply(Window.<Flight> into(SlidingWindows//
        .of(averagingInterval)//
        .every(averagingFrequency))//
        /*.triggering(Repeatedly.forever(
            AfterWatermark.pastEndOfWindow()
            .withLateFirings(
                AfterPane.elementCountAtLeast(10))
            .orFinally(AfterProcessingTime.pastFirstElementInPane()
                .plusDelayOf(Duration.standardMinutes(10)))))*/);

    PCollection<KV<String, Double>> avgArrDelay = CreateTrainingDataset.computeAverageArrivalDelay(hourlyFlights);

    hourlyFlights = CreateTrainingDataset.addDelayInformation(hourlyFlights, avgDepDelay, avgArrDelay, averagingFrequency);

    io.writeFlights(hourlyFlights, options);

    PipelineResult result = p.run();
    if (!options.isRealtime()) {
      result.waitUntilFinish();
    }
  }
}
