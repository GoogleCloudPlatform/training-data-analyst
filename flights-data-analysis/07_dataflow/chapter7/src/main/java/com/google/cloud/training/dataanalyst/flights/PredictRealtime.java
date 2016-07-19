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

import org.joda.time.Duration;
import org.joda.time.Instant;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.google.cloud.dataflow.sdk.Pipeline;
import com.google.cloud.dataflow.sdk.io.PubsubIO;
import com.google.cloud.dataflow.sdk.io.TextIO;
import com.google.cloud.dataflow.sdk.options.DataflowPipelineOptions;
import com.google.cloud.dataflow.sdk.options.Default;
import com.google.cloud.dataflow.sdk.options.Description;
import com.google.cloud.dataflow.sdk.options.PipelineOptionsFactory;
import com.google.cloud.dataflow.sdk.runners.DataflowPipelineRunner;
import com.google.cloud.dataflow.sdk.transforms.DoFn;
import com.google.cloud.dataflow.sdk.transforms.Mean;
import com.google.cloud.dataflow.sdk.transforms.ParDo;
import com.google.cloud.dataflow.sdk.transforms.View;
import com.google.cloud.dataflow.sdk.transforms.windowing.SlidingWindows;
import com.google.cloud.dataflow.sdk.transforms.windowing.Window;
import com.google.cloud.dataflow.sdk.values.KV;
import com.google.cloud.dataflow.sdk.values.PCollection;
import com.google.cloud.dataflow.sdk.values.PCollectionView;

/**
 * A dataflow pipeline to predict whether a flight will be delayed by 15 or more
 * minutes.
 * 
 * @author vlakshmanan
 *
 */
public class PredictRealtime {
	
	@SuppressWarnings("serial")
	public static class ParseFlights extends DoFn<String, Flight> {
		public static final int INVALID_HOUR = -1000;
		private final PCollectionView<Map<String, Double>> delays;
		private final boolean streaming;
		
		public ParseFlights(PCollectionView<Map<String, Double>> delays, boolean streaming) {
			super();
			this.delays = delays;
			this.streaming = streaming;
		}

		@Override
		public void processElement(ProcessContext c) throws Exception {
			String line = c.element();
			try {
				String[] fields = line.split(",");
				if (fields[22].length() == 0 || fields[0].equals("FL_DATE")) {
					return; // delayed/canceled
				}

				Flight f = new Flight();
				f.line = line;
				f.date = fields[0];
				f.fromAirport = fields[8];
				f.toAirport = fields[12];
				f.depHour = Integer.parseInt(fields[13]) / 100; // 2358 -> 23
				f.arrHour = INVALID_HOUR;
				f.departureDelay = Double.parseDouble(fields[15]);
				f.taxiOutTime = Double.parseDouble(fields[16]);
				f.distance = Double.parseDouble(fields[26]);
				f.arrivalDelay = Double.NaN;
				Double d = c.sideInput(delays).get(f.fromAirport + ":" + f.depHour);
				f.averageDepartureDelay = (d == null) ? 0 : d;
				f.averageArrivalDelay = Double.NaN;
				
				if (!streaming || fields[21].length() == 0) {
					// without arrival time: for prediction
					c.outputWithTimestamp(f, toInstant(fields[0], fields[13]));
				}
				
				if (!streaming || fields[21].length() > 0) {
					// with arrival time: for computing avg arrival delay
					f.arrHour = Integer.parseInt(fields[21]) / 100;
					f.arrivalDelay = Double.parseDouble(fields[22]);
					c.outputWithTimestamp(f, toInstant(fields[0], fields[21]));
				}
			} catch (Exception e) {
				LOG.warn("Malformed line {" + line + "} skipped", e);
			}
		}

	}

	private static final Logger LOG = LoggerFactory.getLogger(PredictRealtime.class);

	public static interface MyOptions extends DataflowPipelineOptions {
		@Description("Path of the file to read from")
		@Default.String("/Users/vlakshmanan/data/flights/small.csv")
		String getInput();

		void setInput(String s);

		@Description("Path of the output directory")
		@Default.String("/tmp/output/")
		String getOutput();

		void setOutput(String s);

		@Description("Path of delay files")
		@Default.String("gs://cloud-training-demos/flights/chapter07/")
		// @Default.String("/Users/vlakshmanan/data/flights/")
		String getDelayPath();

		void setDelayPath(String s);

		@Description("Path of tensorflow trained file")
		@Default.String("gs://cloud-training-demos/flights/chapter07/trained_model.tf")
		// "/Users/vlakshmanan/code/training-data-analyst/flights-data-analysis/09_realtime/trained_model.tf")
		String getModelfile();

		void setModelfile(String s);

		@Description("Path of tensorflow graph")
		@Default.String("gs://cloud-training-demos/flights/chapter07/trained_model.proto")
		// "/Users/vlakshmanan/code/training-data-analyst/flights-data-analysis/09_realtime/trained_model.proto")
		String getGraphfile();

		void setGraphfile(String s);
	}

	@SuppressWarnings("serial")
	public static void main(String[] args) {
		// create pipeline from options
		MyOptions options = PipelineOptionsFactory.fromArgs(args).withValidation().as(MyOptions.class);
		boolean streaming = options.getInput().contains("/topics/");
		if (streaming) {
			LOG.info("Creating real-time pipeline that reads from Pub/Sub I/O");
			options.setStreaming(true);
			options.setRunner(DataflowPipelineRunner.class);
		}
		Pipeline p = Pipeline.create(options);

		// read delays-*.csv into memory for use as a side-input
		PCollectionView<Map<String, Double>> delays = getAverageDelays(p, options.getDelayPath());

		// read flights, either batch or in 1-hr windows every minute
		PCollection<String> lines;
		if (streaming) {
			// real-time for pub-sub
			lines = p.apply("ReadLines", PubsubIO.Read.topic(options.getInput())) //
					.apply("window",
							Window.into(SlidingWindows//
									.of(Duration.standardMinutes(60))//
									.every(Duration.standardMinutes(1))));
		} else {
			// batch, from text
			lines = p.apply("ReadLines", TextIO.Read.from(options.getInput()));
		}

		PCollection<Flight> flights = lines.apply("ParseFlights",
				ParDo.withSideInputs(delays).of(new ParseFlights(delays, streaming))) //
		;

		PCollectionView<Map<String, Double>> arrDelay = flights
				.apply("airport:hour", ParDo.of(new DoFn<Flight, KV<String, Double>>() {

					@Override
					public void processElement(ProcessContext c) throws Exception {
						Flight f = c.element();
						if (f.arrHour != ParseFlights.INVALID_HOUR) {
							String key = "arr_" + f.toAirport + ":" + f.date + ":" + f.arrHour;
							double value = f.arrivalDelay;
							c.output(KV.of(key, value));
						}
					}

				})) //
				.apply(Mean.perKey()) //
				.apply(View.asMap());
		
		PCollection<String> pred =
		flights.apply("Predict", ParDo.withSideInputs(arrDelay).of(new DoFn<Flight, String>() {

			// FIXME: distribute predictions to different machines
			transient TensorflowModel tfModel = new TensorflowModel(options.getModelfile(), options.getGraphfile());
			
			@Override
			public void processElement(ProcessContext c) throws Exception {
				Flight f = c.element();
				if (f.arrHour == ParseFlights.INVALID_HOUR) {
					// don't know when this flight is arriving, so predict ...
					f = f.newCopy();
					// get average arrival delay
					String key = "arr_" + f.toAirport + ":" + f.date + ":" + (f.depHour - 1);
					Double delay = c.sideInput(arrDelay).get(key);
					f.averageArrivalDelay = (delay == null) ? 0 : delay;

					// predict
					boolean ontime = tfModel.predict(f.getInputFeatures()) > 0.5;

					// output
					c.output(f.line + "," + ontime);
				}
			}
		}));
		
		if (streaming) {
			pred.apply("WriteFlights", PubsubIO.Write.topic(options.getOutput()));
		} else {
			pred.apply("WriteFlights", TextIO.Write.to(options.getOutput() + "flights").withSuffix(".csv"));
		}
		
		p.run();
	}

	public static Instant toInstant(String date, String hourmin) {
		// e.g: 2015-01-01 and 0837
		int hrmin = Integer.parseInt(hourmin);
		int hr = hrmin / 100;
		int min = hrmin % 100;
		return Instant.parse(date) //
				.plus(Duration.standardHours(hr)) //
				.plus(Duration.standardMinutes(min));
	}

	@SuppressWarnings("serial")
	private static PCollectionView<Map<String, Double>> getAverageDelays(Pipeline p, String path) {
		return p.apply("Read delays-*.csv", TextIO.Read.from(path + "delays-*.csv")) //
				.apply("Parse delays-*.csv", ParDo.of(new DoFn<String, KV<String, Double>>() {
					@Override
					public void processElement(ProcessContext c) throws Exception {
						String line = c.element();
						String[] fields = line.split(",");
						c.output(KV.of(fields[0], Double.parseDouble(fields[1])));
					}
				})) //
				.apply("toView", View.asMap());
	}
}
