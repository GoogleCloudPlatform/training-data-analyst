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

import org.apache.beam.sdk.Pipeline;
import org.apache.beam.sdk.io.TextIO;
import org.apache.beam.sdk.io.gcp.bigquery.BigQueryIO;
import org.apache.beam.sdk.options.Default;
import org.apache.beam.sdk.options.Description;
import org.apache.beam.sdk.options.PipelineOptions;
import org.apache.beam.sdk.options.PipelineOptionsFactory;
import org.apache.beam.sdk.transforms.DoFn;
import org.apache.beam.sdk.transforms.Mean;
import org.apache.beam.sdk.transforms.ParDo;
import org.apache.beam.sdk.transforms.View;
import org.apache.beam.sdk.values.KV;
import org.apache.beam.sdk.values.PCollection;
import org.apache.beam.sdk.values.PCollectionView;

import com.google.api.services.bigquery.model.TableRow;
import com.google.cloud.training.flights.Flight.INPUTCOLS;

/**
 * Adds in reading from BigQuery
 * 
 * @author vlakshmanan
 *
 */
public class CreateTrainingDataset6 {

  public static interface MyOptions extends PipelineOptions {
    @Description("Path of the output directory")
    @Default.String("/tmp/output/")
    String getOutput();

    void setOutput(String s);

    @Description("Path of trainday.csv")
    @Default.String("gs://cloud-training-demos-ml/flights/trainday.csv")
    String getTraindayCsvPath();

    void setTraindayCsvPath(String s);
  }

  @SuppressWarnings("serial")
  public static void main(String[] args) {
    MyOptions options = PipelineOptionsFactory.fromArgs(args).withValidation().as(MyOptions.class);
    options.setTempLocation("gs://cloud-training-demos-ml/flights/staging");
    Pipeline p = Pipeline.create(options);

    // read traindays.csv into memory for use as a side-input
    PCollectionView<Map<String, String>> traindays = getTrainDays(p, options.getTraindayCsvPath());

    String query = "SELECT EVENT_DATA FROM flights.simevents "
        + " WHERE STRING(FL_DATE) < '2015-01-04' AND (EVENT = 'wheelsoff' "
        + " OR EVENT = 'arrived') AND UNIQUE_CARRIER = 'AA' " + " ORDER BY NOTIFY_TIME ASC";

    PCollection<Flight> flights = p //
        .apply("ReadLines", BigQueryIO.read().fromQuery(query)) //
        .apply("ParseFlights", ParDo.of(new DoFn<TableRow, Flight>() {
          @ProcessElement
          public void processElement(ProcessContext c) throws Exception {
            TableRow row = c.element();
            String line = (String) row.getOrDefault("EVENT_DATA", "");
            Flight f = Flight.fromCsv(line);
            if (f != null) {
              c.output(f);
            }
          }
        })) //
        .apply("TrainOnly", ParDo.of(new DoFn<Flight, Flight>() {
          @ProcessElement
          public void processElement(ProcessContext c) throws Exception {
            Flight f = c.element();
            String date = f.getField(Flight.INPUTCOLS.FL_DATE);
            boolean isTrainDay = c.sideInput(traindays).containsKey(date);
            if (isTrainDay) {
              c.output(f);
            }
          }
        }).withSideInputs(traindays)) //
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
        .apply("WriteDelays", TextIO.write().to(options.getOutput() + "delays6").withSuffix(".csv").withoutSharding());

    flights.apply("ToCsv", ParDo.of(new DoFn<Flight, String>() {
      @ProcessElement
      public void processElement(ProcessContext c) throws Exception {
        Flight f = c.element();
        if (f.getField(INPUTCOLS.EVENT).equals("arrived")) {
          c.output(f.toTrainingCsv());
        }
      }
    })) //
        .apply("WriteFlights", TextIO.write().to(options.getOutput() + "flights6").withSuffix(".csv").withoutSharding());

    p.run();
  }

  @SuppressWarnings("serial")
  private static PCollectionView<Map<String, String>> getTrainDays(Pipeline p, String path) {
    return p.apply("Read trainday.csv", TextIO.read().from(path)) //
        .apply("Parse trainday.csv", ParDo.of(new DoFn<String, KV<String, String>>() {
          @ProcessElement
          public void processElement(ProcessContext c) throws Exception {
            String line = c.element();
            String[] fields = line.split(",");
            if (fields.length > 1 && "True".equals(fields[1])) {
              c.output(KV.of(fields[0], "True")); // ignore value
            }
          }
        })) //
        .apply("toView", View.asMap());
  }
}
