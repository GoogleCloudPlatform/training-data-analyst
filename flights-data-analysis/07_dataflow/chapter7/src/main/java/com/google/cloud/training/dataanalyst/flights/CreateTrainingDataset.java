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

import java.io.Serializable;
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
public class CreateTrainingDataset {

	private static final Logger LOG = LoggerFactory.getLogger(CreateTrainingDataset.class);

	public static interface MyOptions extends PipelineOptions {
		@Description("Path of the file to read from")
		@Default.String("/Users/vlakshmanan/data/flights/small.csv")
		String getInput();

		void setInput(String s);

		@Description("Path of the trainday.csv file")
		@Default.String("gs://cloud-training-demos/flights/trainday.csv")
		String getTraindaysPath();

		void setTraindaysPath(String s);

		@Description("Path of the output directory")
		@Default.String("/tmp/flights/chapter07")
		String getOutput();

		void setOutput(String s);
	}

	@SuppressWarnings("serial")
	public static class Flight implements Serializable {
		String date;
		String fromAirport;
		String toAirport;
		int depHour;
		int arrHour;
		double departureDelay;
		double taxiOutTime;
		double distance;
		double arrivalDelay;
		double averageDepartureDelay;
		double averageArrivalDelay;

		public Flight newCopy() {
			Flight f = new Flight();
			f.date = this.date;
			f.fromAirport = this.fromAirport;
			f.toAirport = this.toAirport;
			f.depHour = this.depHour;
			f.arrHour = this.arrHour;
			f.departureDelay = this.departureDelay;
			f.taxiOutTime = this.taxiOutTime;
			f.distance = this.distance;
			f.arrivalDelay = this.arrivalDelay;
			f.averageDepartureDelay = this.averageDepartureDelay;
			f.averageArrivalDelay = this.averageArrivalDelay;
			return f;
		}

		public double[] getInputFeatures() {
			return new double[] { departureDelay, taxiOutTime, distance, averageDepartureDelay, averageArrivalDelay };
		}

		public String toTrainingCsv() {
			double[] features = this.getInputFeatures();
			boolean ontime = this.arrivalDelay < 15;
			StringBuilder sb = new StringBuilder();
			sb.append(ontime ? 1.0 : 0.0);
			sb.append(",");
			for (int i = 0; i < features.length; ++i) {
				sb.append(features[i]);
				sb.append(",");
			}
			sb.deleteCharAt(sb.length() - 1); // last comma
			return sb.toString();
		}
	}

	@SuppressWarnings("serial")
	public static class SelectFields extends DoFn<String, Flight> {
		final PCollectionView<Map<String, String>> traindays;

		public SelectFields(PCollectionView<Map<String, String>> traindays) {
			super();
			this.traindays = traindays;
		}

		@Override
		public void processElement(ProcessContext c) {
			String line = c.element();
			try {
				String[] fields = line.split(",");
				if (fields[22].length() == 0) {
					return; // delayed/canceled
				}

				boolean isTrainDay = c.sideInput(traindays).containsKey(fields[0]);

				if (isTrainDay) {
					// get values only for train days
					Flight f = new Flight();
					f.date = fields[0];
					f.fromAirport = fields[8];
					f.toAirport = fields[12];
					f.depHour = Integer.parseInt(fields[13]) / 100; // 2358 ->
																	// 23
					f.arrHour = Integer.parseInt(fields[21]) / 100; // 2358 ->
																	// 23
					f.departureDelay = Double.parseDouble(fields[15]);
					f.taxiOutTime = Double.parseDouble(fields[16]);
					f.distance = Double.parseDouble(fields[26]);
					f.arrivalDelay = Double.parseDouble(fields[22]);
					f.averageDepartureDelay = f.averageArrivalDelay = Double.NaN;

					// int arrivalTime = Integer.parseInt(fields[21]); // e.g.
					// 2358
					// int hour = arrivalTime / 100;
					// int minutes = arrivalTime % 100;
					// Instant t = Instant.parse(f.date).plus((hour*60 +
					// minutes)*60*1000L);
					// c.outputWithTimestamp(f, t);

					c.output(f);
				}
			} catch (Exception e) {
				LOG.warn("Malformed line {" + line + "} skipped", e);
			}
		}
	}

	@SuppressWarnings("serial")
	public static void main(String[] args) {
		MyOptions options = PipelineOptionsFactory.fromArgs(args).withValidation().as(MyOptions.class);
		Pipeline p = Pipeline.create(options);

		// read traindays.csv into memory for use as a side-input
		PCollectionView<Map<String, String>> traindays = getTrainDays(p, options.getTraindaysPath());

		// read the data file, filtering by traindays
		PCollection<Flight> flights = p //
				.apply(TextIO.Read.from(options.getInput())) // read
				.apply("SelectFields", ParDo.withSideInputs(traindays).of(new SelectFields(traindays)));

		// group by from-airport and hour; compute mean taxiout delay
		// group by to-airport, date+hour; compute "current" arrival delay
		PCollection<KV<String, Double>> avgDelay = flights //
				.apply("GroupByAirportAndHour", ParDo.of(new DoFn<Flight, KV<String, Double>>() {
					@Override
					public void processElement(ProcessContext c) throws Exception {
						Flight f = c.element();
						String key = f.fromAirport + ":" + f.depHour;
						c.output(KV.of(key, f.departureDelay + f.taxiOutTime));

						key = f.toAirport + ":" + f.arrHour + " on " + f.date;
						c.output(KV.of(key, f.arrivalDelay));
					}
				})) // (fromAirport + hour) -> (dep-delay + taxiout time)
				.apply(Mean.<String, Double> perKey()); // average delay

		// write out, just to check
		avgDelay.apply(ParDo.of(new DoFn<KV<String, Double>, String>() {
			@Override
			public void processElement(ProcessContext c) throws Exception {
				c.output(c.element().getKey() + " ->  " + c.element().getValue());
			}
		})).apply(TextIO.Write.to(options.getOutput() + "/delay").withSuffix(".txt"));

		// add average departure to each flight
		PCollectionView<Map<String, Double>> avgDelayLookup = avgDelay.apply(View.asMap());
		flights = flights.apply("AddAvgDelay", ParDo.withSideInputs(avgDelayLookup).of(new DoFn<Flight, Flight>() {

			@Override
			public void processElement(ProcessContext c) throws Exception {
				Flight f = c.element().newCopy();

				// get typical departure delay at from airport
				String key = f.fromAirport + ":" + f.depHour;
				Double depDelay = c.sideInput(avgDelayLookup).get(key);
				f.averageDepartureDelay = (depDelay != null) ? depDelay : 0;

				// get "current" arrival delay that is known at departure time!
				key = f.toAirport + ":" + (f.depHour - 1) + " on " + f.date;
				Double arrDelay = c.sideInput(avgDelayLookup).get(key);
				f.averageArrivalDelay = (arrDelay != null) ? arrDelay : 0;

				c.output(f);
			}

		}));

		// write out training data
		flights.apply("ToCsv", ParDo.of(new DoFn<Flight, String>() {
			@Override
			public void processElement(ProcessContext c) throws Exception {
				Flight f = c.element();
				c.output(f.toTrainingCsv());
			}
		})).apply(TextIO.Write.named("WriteResult").to(options.getOutput() + "/train").withSuffix(".csv"));

		// run the pipeline
		p.run();
	}

	@SuppressWarnings("serial")
	private static PCollectionView<Map<String, String>> getTrainDays(Pipeline p, String traindaysPath) {
		PCollection<KV<String, String>> days = p //
				.apply(TextIO.Read.from(traindaysPath)) // read
				.apply("ReadTrainDays", ParDo.of(new DoFn<String, KV<String, String>>() {
					@Override
					public void processElement(ProcessContext c) throws Exception {
						String line = c.element();
						String[] fields = line.split(",");
						if (fields.length > 1 && "True".equals(fields[1])) {
							c.output(KV.of(fields[0], ""));
						}
					}
				}));

		return days.apply(View.asMap());
	}

}
