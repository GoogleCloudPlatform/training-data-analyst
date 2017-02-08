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

package com.google.cloud.training.dataanalyst.flights;

import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.google.cloud.dataflow.sdk.Pipeline;
import com.google.cloud.dataflow.sdk.io.TextIO;
import com.google.cloud.dataflow.sdk.options.Default;
import com.google.cloud.dataflow.sdk.options.Description;
import com.google.cloud.dataflow.sdk.options.PipelineOptions;
import com.google.cloud.dataflow.sdk.options.PipelineOptionsFactory;
import com.google.cloud.dataflow.sdk.transforms.DoFn;
import com.google.cloud.dataflow.sdk.transforms.Mean;
import com.google.cloud.dataflow.sdk.transforms.ParDo;
import com.google.cloud.dataflow.sdk.transforms.View;
import com.google.cloud.dataflow.sdk.values.KV;
import com.google.cloud.dataflow.sdk.values.PCollection;
import com.google.cloud.dataflow.sdk.values.PCollectionView;

/**
 * A dataflow pipeline to create the training dataset to predict whether a
 * flight will be delayed by 15 or more minutes. The key thing that this
 * pipeline does is to add the average delays for the from & to airports at this
 * hour to the set of training features.
 * 
 * @author vlakshmanan
 *
 */
public class CreateTrainingTestDataset {
	@SuppressWarnings("serial")
	public static class ParseFlights extends DoFn<String, Flight> {
		private final PCollectionView<Map<String, String>> traindays;

		public ParseFlights(PCollectionView<Map<String, String>> traindays) {
			super();
			this.traindays = traindays;
		}

		@Override
		public void processElement(ProcessContext c) throws Exception {
			String line = c.element();
			try {
				String[] fields = line.split(",");
				if (fields[22].length() == 0) {
					return; // delayed/canceled
				}

				Flight f = new Flight();
				f.date = fields[0];

				boolean isTrainDay = c.sideInput(traindays).containsKey(f.date);
				if (!isTrainDay) {
					LOG.debug("Ignoring " + f.date + " as it is not a trainday");
					return;
				}

				f.fromAirport = fields[8];
				f.toAirport = fields[12];
				f.depHour = Integer.parseInt(fields[13]) / 100; // 2358 -> 23
				f.arrHour = Integer.parseInt(fields[21]) / 100;
				f.departureDelay = Double.parseDouble(fields[15]);
				f.taxiOutTime = Double.parseDouble(fields[16]);
				f.distance = Double.parseDouble(fields[26]);
				f.arrivalDelay = Double.parseDouble(fields[22]);
				f.averageDepartureDelay = f.averageArrivalDelay = Double.NaN;
				c.output(f);
			} catch (Exception e) {
				LOG.warn("Malformed line {" + line + "} skipped", e);
			}
		}

	}

	private static final Logger LOG = LoggerFactory.getLogger(CreateTrainingTestDataset.class);

	public static interface MyOptions extends PipelineOptions {
		@Description("Path of the file to read from")
		@Default.String("/Users/vlakshmanan/data/flights/small.csv")
		String getInput();

		void setInput(String s);

		@Description("Path of the output directory")
		@Default.String("/tmp/output/")
		String getOutput();

		void setOutput(String s);

		@Description("Path of trainday.csv")
		@Default.String("gs://cloud-training-demos/flights/trainday.csv")
		String getTraindayCsvPath();

		void setTraindayCsvPath(String s);
	}

	@SuppressWarnings("serial")
	public static void main(String[] args) {
		MyOptions options = PipelineOptionsFactory.fromArgs(args).withValidation().as(MyOptions.class);
		Pipeline p = Pipeline.create(options);

		// read traindays.csv into memory for use as a side-input
		PCollectionView<Map<String, String>> traindays = getTrainingDays(p, options.getTraindayCsvPath());

		PCollection<Flight> flights = p //
				.apply("ReadLines", TextIO.Read.from(options.getInput())) //
				.apply("ParseFlights", ParDo.withSideInputs(traindays).of(new ParseFlights(traindays))) //
		;

		PCollection<KV<String, Double>> delays = flights
				.apply("airport:hour", ParDo.of(new DoFn<Flight, KV<String, Double>>() {

					@Override
					public void processElement(ProcessContext c) throws Exception {
						Flight f = c.element();
						String key = f.fromAirport + ":" + f.depHour;
						double value = f.departureDelay + f.taxiOutTime;
						c.output(KV.of(key, value));
						key = "arr_" + f.toAirport + ":" + f.date + ":" + f.arrHour;
						value = f.arrivalDelay;
						c.output(KV.of(key, value));
					}

				})) //
				.apply(Mean.perKey());

		delays.apply("DelayToCsv", ParDo.of(new DoFn<KV<String, Double>, String>() {
			@Override
			public void processElement(ProcessContext c) throws Exception {
				KV<String, Double> kv = c.element();
				if (!kv.getKey().startsWith("arr_")){
					c.output(kv.getKey() + "," + kv.getValue());
				}
			}
		})) //
				.apply("WriteDelays", TextIO.Write.to(options.getOutput() + "delays").withSuffix(".csv"));

		PCollectionView<Map<String, Double>> avgDelay = delays.apply(View.asMap());
		flights = flights.apply("AddDelayInfo", ParDo.withSideInputs(avgDelay).of(new DoFn<Flight, Flight>() {

			@Override
			public void processElement(ProcessContext c) throws Exception {
				Flight f = c.element().newCopy();
				String key = f.fromAirport + ":" + f.depHour;
				Double delay = c.sideInput(avgDelay).get(key);
				f.averageDepartureDelay = (delay == null)? 0 : delay;
				key = "arr_" + f.toAirport + ":" + f.date + ":" + (f.depHour-1);
				delay = c.sideInput(avgDelay).get(key);
				f.averageArrivalDelay = (delay == null)? 0 : delay;
				c.output(f);
			}

		}));

		writeCsv(flights, "flights", options);
		
		// write test data also, but using departure delay statistics computed on training data
		PCollectionView<Map<String, String>> testdays = getTestDays(p, options.getTraindayCsvPath());
		PCollection<Flight> testflights = p //
				.apply("ReadLinesT", TextIO.Read.from(options.getInput())) //
				.apply("ParseFlightsT", ParDo.withSideInputs(testdays).of(new ParseFlights(testdays))) //
		;
		PCollectionView<Map<String, Double>> avgArrDelay = testflights
				.apply("airport:hour", ParDo.of(new DoFn<Flight, KV<String, Double>>() {
					@Override
					public void processElement(ProcessContext c) throws Exception {
						Flight f = c.element();
						// only arrival delay!
						String key = "arr_" + f.toAirport + ":" + f.date + ":" + f.arrHour;
						double value = f.arrivalDelay;
						c.output(KV.of(key, value));
					}
				})) //
				.apply(Mean.perKey()).apply(View.asMap());
		
		testflights = testflights.apply("AddDelayInfoT",
				ParDo.withSideInputs(avgDelay, avgArrDelay).of(new DoFn<Flight, Flight>() {
						@Override
						public void processElement(ProcessContext c) throws Exception {
							Flight f = c.element().newCopy();
							String key = f.fromAirport + ":" + f.depHour;
							Double delay = c.sideInput(avgDelay).get(key); // from training data
							f.averageDepartureDelay = (delay == null)? 0 : delay;
							key = "arr_" + f.toAirport + ":" + f.date + ":" + (f.depHour-1);
							delay = c.sideInput(avgArrDelay).get(key); // from test data (causal)
							f.averageArrivalDelay = (delay == null)? 0 : delay;
							c.output(f);
						}
					}));
		
		writeCsv(testflights, "testflights", options);
		
		p.run();
	}

	@SuppressWarnings("serial")
	private static void writeCsv(PCollection<Flight> flights, String prefix, MyOptions options) {
		flights.apply("ToCsv", ParDo.of(new DoFn<Flight, String>() {
			@Override
			public void processElement(ProcessContext c) throws Exception {
				Flight f = c.element();
				c.output(f.toTrainingCsv());
			}
		})) //
				.apply("WriteFlights", TextIO.Write.to(options.getOutput() + prefix).withSuffix(".csv"));
	}

	@SuppressWarnings("serial")
	private static PCollectionView<Map<String, String>> getDaysThatMatch(Pipeline p, String path, String fieldValue) {
		return p.apply("Read trainday.csv", TextIO.Read.from(path)) //
				.apply("Parse trainday.csv", ParDo.of(new DoFn<String, KV<String, String>>() {
					@Override
					public void processElement(ProcessContext c) throws Exception {
						String line = c.element();
						String[] fields = line.split(",");
						if (fields.length > 1 && fieldValue.equals(fields[1])) {
							c.output(KV.of(fields[0], "")); // ignore value
						}
					}
				})) //
				.apply("toView", View.asMap());
	}
	
	private static PCollectionView<Map<String, String>> getTrainingDays(Pipeline p, String path) {
		return getDaysThatMatch(p, path, "True");
	}
	
	private static PCollectionView<Map<String, String>> getTestDays(Pipeline p, String path) {
		return getDaysThatMatch(p, path, "False");
	}
}
