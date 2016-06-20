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
 * pipeline does is to add the average taxiout delay for this airport at this
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
	}

	@SuppressWarnings("serial")
	public static class Flight implements Serializable {
		String date;
		String fromAirport;
		int hour;
		double departureDelay;
		double taxiOutTime;
		double distance;
		double arrivalDelay;
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
					f.hour = Integer.parseInt(fields[13].substring(1, 5)) / 100;
					f.departureDelay = Double.parseDouble(fields[15]);
					f.taxiOutTime = Double.parseDouble(fields[16]);
					f.distance = Double.parseDouble(fields[26]);
					f.arrivalDelay = Double.parseDouble(fields[22]);
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
		PCollection<KV<String, Double>> delayByAirport = flights //
				.apply("GroupByFromAirportAndHour", ParDo.of(new DoFn<Flight, KV<String, Double>>() {
					@Override
					public void processElement(ProcessContext c) throws Exception {
						Flight f = c.element();
						String key = f.fromAirport + ":" + f.hour;
						c.output(KV.of(key, f.departureDelay + f.taxiOutTime));
					}
				})) // (fromAirport + hour) -> (dep-delay + taxiout time)
				.apply(Mean.<String, Double> perKey()); // average delay
														// for key

		// write out, just to check
		delayByAirport.apply(ParDo.of(new DoFn<KV<String, Double>, String>() {
			@Override
			public void processElement(ProcessContext c) throws Exception {
				c.output(c.element().getKey() + "   " + c.element().getValue());
			}
		})).apply(TextIO.Write.named("WriteResult").to("/tmp/output").withSuffix(".txt"));

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
							LOG.info("train: " + fields[0]);
							c.output(KV.of(fields[0], ""));
						}
					}
				}));

		return days.apply(View.asMap());
	}

}
