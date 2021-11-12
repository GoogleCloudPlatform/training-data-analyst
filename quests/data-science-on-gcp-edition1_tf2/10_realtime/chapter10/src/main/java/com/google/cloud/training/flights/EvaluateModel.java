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

import java.text.DecimalFormat;
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
import org.apache.beam.sdk.values.KV;
import org.apache.beam.sdk.values.PCollection;
import org.apache.beam.sdk.values.PCollectionView;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.google.cloud.training.flights.Flight.INPUTCOLS;

/**
 * Evaluate ML model.
 * 
 * @author vlakshmanan
 *
 */
@SuppressWarnings("serial")
public class EvaluateModel {
  private static final Logger LOG = LoggerFactory.getLogger(EvaluateModel.class);

  public static interface MyOptions extends DataflowPipelineOptions {
    @Description("Should we process the full dataset or just a small sample?")
    @Default.Boolean(false)
    boolean getFullDataset();

    void setFullDataset(boolean b);
    
    @Description("Bucket name")
    @Default.String("cloud-training-demos-ml")
    String getBucket();
    
    void setBucket(String s);
  }
  
  private static String getDelayPath(MyOptions opts) {
    return "gs://BUCKET/flights/chapter8/output/delays.csv".replace("BUCKET", opts.getBucket());
  }

  private static String getOutput(MyOptions opts) {
    return "gs://BUCKET/flights/chapter10/eval/".replace("BUCKET", opts.getBucket());
  }

  private static String getTempLocation(MyOptions opts) {
    return "gs://BUCKET/flights/staging".replace("BUCKET", opts.getBucket());
  }
  
  public static void main(String[] args) {
    MyOptions options = PipelineOptionsFactory.fromArgs(args).withValidation().as(MyOptions.class);
    if (options.getFullDataset()) {
      options.setRunner(DataflowRunner.class);
    }
    options.setTempLocation(getTempLocation(options));

    Pipeline p = Pipeline.create(options);

    String query = "SELECT EVENT_DATA FROM flights2016.simevents WHERE ";
    if (!options.getFullDataset()) {
      query += " STRING(FL_DATE) < '2016-01-02' AND ";
    }
    query += " (EVENT = 'wheelsoff' OR EVENT = 'arrived') ";
    LOG.info(query);

    PCollection<Flight> allFlights = CreateTrainingDataset.readFlights(p, query);

    PCollectionView<Map<String, Double>> avgDepDelay = AddRealtimePrediction.readAverageDepartureDelay(p, getDelayPath(options));

    PCollection<Flight> hourlyFlights = CreateTrainingDataset.applyTimeWindow(allFlights);

    PCollection<KV<String, Double>> avgArrDelay = CreateTrainingDataset.computeAverageArrivalDelay(hourlyFlights);

    hourlyFlights = CreateTrainingDataset.addDelayInformation(//
        hourlyFlights, avgDepDelay, avgArrDelay, CreateTrainingDataset.AVERAGING_FREQUENCY);
    
    // keep only the "arrived" events for evaluation
    PCollection<Flight> arrivedFlights = //
        hourlyFlights.apply("arrived", ParDo.of(new DoFn<Flight, Flight>() {
      @ProcessElement
      public void processElement(ProcessContext c) throws Exception {
        Flight f = c.element();
        if (f.getField(INPUTCOLS.EVENT).equals("arrived")) {
          c.output(f);
        }
      }
    }));
    
    // do predictions
    PCollection<FlightPred> preds = InputOutput.addPredictionInBatches(arrivedFlights, true);
    
    // write out
    preds.apply("ToCsv", ParDo.of(new DoFn<FlightPred, String>() {
      @ProcessElement
      public void processElement(ProcessContext c) throws Exception {
        FlightPred fp = c.element();
        c.output(toEvalCsv(fp));
      }
    })) //
    .apply("Write", TextIO.write().to(getOutput(options) + "evalFlights").withSuffix(".csv"));
    
    PipelineResult result = p.run();
    if (!options.getFullDataset()) {
      // for small datasets, block
      result.waitUntilFinish();
    }
  }

  private static String toEvalCsv(FlightPred fp) {
    return new DecimalFormat("0.00").format(fp.ontime) + "," + fp.flight.toTrainingCsv();
  }
}
