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
import org.apache.beam.sdk.io.gcp.bigquery.BigQueryIO;
import org.apache.beam.sdk.options.Default;
import org.apache.beam.sdk.options.Description;
import org.apache.beam.sdk.options.PipelineOptionsFactory;
import org.apache.beam.sdk.transforms.DoFn;
import org.apache.beam.sdk.transforms.Mean;
import org.apache.beam.sdk.transforms.ParDo;
import org.apache.beam.sdk.transforms.View;
import org.apache.beam.sdk.transforms.join.CoGbkResult;
import org.apache.beam.sdk.transforms.join.CoGroupByKey;
import org.apache.beam.sdk.transforms.join.KeyedPCollectionTuple;
import org.apache.beam.sdk.transforms.windowing.IntervalWindow;
import org.apache.beam.sdk.transforms.windowing.SlidingWindows;
import org.apache.beam.sdk.transforms.windowing.Window;
import org.apache.beam.sdk.values.KV;
import org.apache.beam.sdk.values.PCollection;
import org.apache.beam.sdk.values.PCollectionView;
import org.apache.beam.sdk.values.TupleTag;
import org.joda.time.Duration;
import org.joda.time.Instant;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.google.api.services.bigquery.model.TableRow;
import com.google.cloud.training.flights.Flight.INPUTCOLS;

/**
 * Efficient version that uses CoGroupByKey.
 * 
 * @author vlakshmanan
 *
 */
@SuppressWarnings("serial")
public class CreateTrainingDataset {
  private static final Logger LOG = LoggerFactory.getLogger(CreateTrainingDataset.class);

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
  
  private static String getOutput(MyOptions opts) {
    return "gs://BUCKET/flights/chapter8/output/".replace("BUCKET", opts.getBucket());
  }

  private static String getTraindayCsvPath(MyOptions opts) {
    return "gs://BUCKET/flights/trainday.csv".replace("BUCKET", opts.getBucket());
  }
  
  private static String getTempLocation(MyOptions opts) {
    return "gs://BUCKET/flights/staging".replace("BUCKET", opts.getBucket());
  }

  final static Duration AVERAGING_INTERVAL = Duration.standardHours(1);
  final static Duration AVERAGING_FREQUENCY = Duration.standardMinutes(5);
  public static void main(String[] args) {
    MyOptions options = PipelineOptionsFactory.fromArgs(args).withValidation().as(MyOptions.class);
    // options.setStreaming(true);
    options.setRunner(DataflowRunner.class);
    options.setTempLocation(getTempLocation(options));
    Pipeline p = Pipeline.create(options);

    // read traindays.csv into memory for use as a side-input
    PCollectionView<Map<String, String>> traindays = getTrainDays(p, getTraindayCsvPath(options));

    String query = "SELECT EVENT_DATA FROM flights.simevents WHERE ";
    if (!options.getFullDataset()) {
      query += " STRING(FL_DATE) < '2015-01-04' AND ";
    }
    query += " (EVENT = 'wheelsoff' OR EVENT = 'arrived') ";
    LOG.info(query);

    PCollection<Flight> allFlights = readFlights(p, query);

    PCollection<KV<String, Double>> depDelays = computeAverageDepartureDelay(allFlights, traindays);

    writeDepartureDelays(depDelays, options);

    PCollectionView<Map<String, Double>> avgDepDelay = depDelays.apply("depdelay->map", View.asMap());

    PCollection<Flight> hourlyFlights = allFlights.apply(Window.<Flight> into(SlidingWindows//
        .of(AVERAGING_INTERVAL)//
        .every(AVERAGING_FREQUENCY))); // .discardingFiredPanes());

    PCollection<KV<String, Double>> avgArrDelay = computeAverageArrivalDelay(hourlyFlights);

    hourlyFlights = addDelayInformation(hourlyFlights, avgDepDelay, avgArrDelay);

    for (String name : new String[] { "train", "test" }) {
      boolean isTrain = name.equals("train");
      PCollection<Flight> outFlights = filterTrainOrTest(name, hourlyFlights, traindays, isTrain);
      writeFlights(name, outFlights, options);
    }

    PipelineResult result = p.run();
    if (!options.getFullDataset()) {
      // for small datasets, block
      result.waitUntilFinish();
    }
  }

  private static PCollection<KV<String, Double>> computeAverageDepartureDelay(PCollection<Flight> allFlights,
      PCollectionView<Map<String, String>> traindays) {
    PCollection<KV<String, Double>> depDelays = //
        filterTrainOrTest("globalTrain", allFlights, traindays, true) //
            .apply("airport:hour->depdelay", ParDo.of(new DoFn<Flight, KV<String, Double>>() {

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
    return depDelays;
  }

  private static void writeDepartureDelays(PCollection<KV<String, Double>> depDelays, MyOptions options) {
    depDelays.apply("DepDelayToCsv", ParDo.of(new DoFn<KV<String, Double>, String>() {
      @ProcessElement
      public void processElement(ProcessContext c) throws Exception {
        KV<String, Double> kv = c.element();
        c.output(kv.getKey() + "," + kv.getValue());
      }
    })) //
        .apply("WriteDepDelays", TextIO.write().to(getOutput(options) + "delays").withSuffix(".csv").withoutSharding());
  }

  private static PCollection<Flight> readFlights(Pipeline p, String query) {
    PCollection<Flight> allFlights = p //
        .apply("ReadLines", BigQueryIO.read().fromQuery(query)) //
        .apply("ParseFlights", ParDo.of(new DoFn<TableRow, Flight>() {
          @ProcessElement
          public void processElement(ProcessContext c) throws Exception {
            TableRow row = c.element();
            String line = (String) row.getOrDefault("EVENT_DATA", "");
            Flight f = Flight.fromCsv(line);
            if (f != null) {
              c.outputWithTimestamp(f, f.getEventTimestamp());
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
    return allFlights;
  }

  private static void writeFlights(String name, PCollection<Flight> outFlights, MyOptions options) {
    PCollection<String> lines = outFlights //
        .apply(name + "ToCsv", ParDo.of(new DoFn<Flight, String>() {
          @ProcessElement
          public void processElement(ProcessContext c) throws Exception {
            Flight f = c.element();
            if (f.getField(INPUTCOLS.EVENT).equals("arrived")) {
              c.output(f.toTrainingCsv());
            }
          }
        }));

    // lines = MakeUnique.makeUnique(name, lines);

    lines.apply(name + "Write", TextIO.write().to(getOutput(options) + name + "Flights").withSuffix(".csv"));
  }

  static PCollection<Flight> addDelayInformation(PCollection<Flight> hourlyFlights, //
      PCollectionView<Map<String, Double>> avgDepDelay, //
      PCollection<KV<String, Double>> avgArrDelay) {

    PCollection<KV<String, Flight>> airportFlights = //
        hourlyFlights //
            .apply("InLatestSlice", ParDo.of(new DoFn<Flight, Flight>() {
              @ProcessElement
              public void processElement(ProcessContext c, IntervalWindow window) throws Exception {
                Instant endOfWindow = window.maxTimestamp();
                Instant flightTimestamp = c.timestamp();
                long msecs = endOfWindow.getMillis() - flightTimestamp.getMillis();
                if (msecs < AVERAGING_FREQUENCY.getMillis()) {
                  c.output(c.element());
                }
              }
            }))//
            .apply("AddDepDelay", ParDo.of(new DoFn<Flight, Flight>() {
             
              @ProcessElement
              public void processElement(ProcessContext c) throws Exception {

                Flight f = c.element().newCopy();
                String depKey = f.getField(Flight.INPUTCOLS.ORIGIN) + ":" + f.getDepartureHour();
                Double depDelay = c.sideInput(avgDepDelay).get(depKey);
                f.avgDepartureDelay = (float) ((depDelay == null) ? 0 : depDelay);
                c.output(f);

              }

            }).withSideInputs(avgDepDelay)) //
            .apply("airport->Flight", ParDo.of(new DoFn<Flight, KV<String, Flight>>() {
              @ProcessElement
              public void processElement(ProcessContext c) throws Exception {
                Flight f = c.element();
                String arrKey = f.getField(Flight.INPUTCOLS.DEST);
                c.output(KV.of(arrKey, f));
              }
            }));

    final TupleTag<Flight> t1 = new TupleTag<>();
    final TupleTag<Double> t2 = new TupleTag<>();
    PCollection<Flight> result = KeyedPCollectionTuple //
        .of(t1, airportFlights) //
        .and(t2, avgArrDelay) //
        .apply(CoGroupByKey.create()) //
        .apply("AddArrDelay", ParDo.of(new DoFn<KV<String, CoGbkResult>, Flight>() {
          @ProcessElement
          public void processElement(ProcessContext c) throws Exception {
            Iterable<Flight> flights = c.element().getValue().getAll(t1);
            double avgArrivalDelay = c.element().getValue().getOnly(t2, Double.valueOf(0));
            for (Flight uf : flights) {
              Flight f = uf.newCopy();
              f.avgArrivalDelay = (float) avgArrivalDelay;
              c.output(f);
            }
          }
        }));

    return result;
  }

  static PCollection<KV<String, Double>> computeAverageArrivalDelay(PCollection<Flight> hourlyFlights) {
    PCollection<KV<String, Double>> arrDelays = hourlyFlights
        .apply("airport->arrdelay", ParDo.of(new DoFn<Flight, KV<String, Double>>() {

          @ProcessElement
          public void processElement(ProcessContext c) throws Exception {
            Flight f = c.element();
            if (f.getField(Flight.INPUTCOLS.EVENT).equals("arrived")) {
              try {
                String key = f.getField(Flight.INPUTCOLS.DEST);
                double value = f.getFieldAsFloat(Flight.INPUTCOLS.ARR_DELAY);
                c.output(KV.of(key, value));
              } catch (NumberFormatException e) {
                // ignore exceptions around not being able to parse
              }
            }
          }

        })) //
        .apply("avgArrDelay", Mean.perKey());

    return arrDelays;
  }

  private static PCollection<Flight> filterTrainOrTest(String name, PCollection<Flight> allFlights,
      PCollectionView<Map<String, String>> traindays, boolean trainOnly) {
    return allFlights.apply(name, ParDo.of(new DoFn<Flight, Flight>() {
      @ProcessElement
      public void processElement(ProcessContext c) throws Exception {
        Flight f = c.element();
        String date = f.getField(Flight.INPUTCOLS.FL_DATE);
        boolean isTrainDay = c.sideInput(traindays).containsKey(date);
        if (isTrainDay == trainOnly) {
          c.output(f); // training days only
        }
      }
    }).withSideInputs(traindays));
  }

  private static PCollectionView<Map<String, String>> getTrainDays(Pipeline p, String path) {
    return p.apply("Read trainday.csv", TextIO.read().from(path)) //
        .apply("Parse trainday.csv", ParDo.of(new DoFn<String, KV<String, String>>() {
          @ProcessElement
          public void processElement(ProcessContext c) throws Exception {
            String line = c.element();
            String[] fields = line.split(",");
            if (fields.length > 1 && "True".equals(fields[1])) {
              c.output(KV.of(fields[0], "")); // ignore value
            }
          }
        })) //
        .apply("toView", View.asMap());
  }
}
