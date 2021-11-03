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

import org.apache.beam.sdk.Pipeline;
import org.apache.beam.sdk.io.TextIO;
import org.apache.beam.sdk.options.Default;
import org.apache.beam.sdk.options.Description;
import org.apache.beam.sdk.options.PipelineOptions;
import org.apache.beam.sdk.options.PipelineOptionsFactory;
import org.apache.beam.sdk.transforms.DoFn;
import org.apache.beam.sdk.transforms.Mean;
import org.apache.beam.sdk.transforms.ParDo;
import org.apache.beam.sdk.values.KV;
import org.apache.beam.sdk.values.PCollection;

import com.google.cloud.training.flights.Flight.INPUTCOLS;

/**
 * Demonstrates use of key-value pairs and aggregations. Essentially, this is
 * how you do Map-Reduce in Dataflow
 * 
 * @author vlakshmanan
 *
 */
public class CreateTrainingDataset4 {
  public static interface MyOptions extends PipelineOptions {
    @Description("Path of the file to read from")
    @Default.String("/Users/vlakshmanan/data/flights/small.csv")
    String getInput();

    void setInput(String s);

    @Description("Path of the output directory")
    @Default.String("/tmp/output/")
    String getOutput();

    void setOutput(String s);
  }

  @SuppressWarnings("serial")
  public static void main(String[] args) {
    MyOptions options = PipelineOptionsFactory.fromArgs(args).withValidation().as(MyOptions.class);
    Pipeline p = Pipeline.create(options);

    PCollection<Flight> flights = p //
        .apply("ReadLines", TextIO.read().from(options.getInput())) //
        .apply("ParseFlights", ParDo.of(new DoFn<String, Flight>() {
          @ProcessElement
          public void processElement(ProcessContext c) throws Exception {
            String line = c.element();
            Flight f = Flight.fromCsv(line);
            if (f != null) {
              c.output(f);
            }
          }
        })) //
        .apply("GoodFlights", ParDo.of(new DoFn<Flight, Flight>() {
          @ProcessElement
          public void processElement(ProcessContext c) throws Exception {
            Flight f = c.element();
            if (f.isNotCancelled() && f.isNotDiverted()) {
              c.output(f);
            }
          }
        }));

    PCollection<KV<String, Double>> delays = flights
        .apply("airport:hour", ParDo.of(new DoFn<Flight, KV<String, Double>>() {

          @ProcessElement
          public void processElement(ProcessContext c) throws Exception {
            Flight f = c.element();
            if (f.getField(Flight.INPUTCOLS.EVENT).equals("wheelsoff")) {
              String key = f.getField(Flight.INPUTCOLS.ORIGIN) + ":" + f.getDepartureHour();
              double value = f.getFieldAsFloat(Flight.INPUTCOLS.DEP_DELAY)
                  + f.getFieldAsFloat(Flight.INPUTCOLS.TAXI_OUT);
              c.output(KV.of(key, value));
            }
          }

        })) //
        .apply("avgDepDelay", Mean.perKey());

    delays.apply("DelayToCsv", ParDo.of(new DoFn<KV<String, Double>, String>() {
      @ProcessElement
      public void processElement(ProcessContext c) throws Exception {
        KV<String, Double> kv = c.element();
        c.output(kv.getKey() + "," + kv.getValue());
      }
    })) //
        .apply("WriteDelays", TextIO.write().to(options.getOutput() + "delays4").withSuffix(".csv").withoutSharding());

    flights.apply("ToCsv", ParDo.of(new DoFn<Flight, String>() {
      @ProcessElement
      public void processElement(ProcessContext c) throws Exception {
        Flight f = c.element();
        if (f.getField(INPUTCOLS.EVENT).equals("arrived")) {
          c.output(f.toTrainingCsv());
        }
      }
    })) //
        .apply("WriteFlights", TextIO.write().to(options.getOutput() + "flights4").withSuffix(".csv").withoutSharding());

    p.run();
  }
}
