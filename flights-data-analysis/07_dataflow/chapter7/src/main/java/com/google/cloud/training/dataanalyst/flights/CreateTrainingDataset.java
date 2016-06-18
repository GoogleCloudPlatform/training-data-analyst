/*
 * Copyright (C) 2015 Google Inc.
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

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.google.cloud.dataflow.sdk.Pipeline;
import com.google.cloud.dataflow.sdk.io.TextIO;
import com.google.cloud.dataflow.sdk.options.Default;
import com.google.cloud.dataflow.sdk.options.Description;
import com.google.cloud.dataflow.sdk.options.PipelineOptions;
import com.google.cloud.dataflow.sdk.options.PipelineOptionsFactory;
import com.google.cloud.dataflow.sdk.transforms.Combine;
import com.google.cloud.dataflow.sdk.transforms.DoFn;
import com.google.cloud.dataflow.sdk.transforms.Max;
import com.google.cloud.dataflow.sdk.transforms.PTransform;
import com.google.cloud.dataflow.sdk.transforms.ParDo;
import com.google.cloud.dataflow.sdk.transforms.SerializableFunction;
import com.google.cloud.dataflow.sdk.values.PCollection;
import com.google.cloud.training.dataanalyst.flights.CreateTrainingDataset.Flight;
import com.google.cloud.training.dataanalyst.flights.CreateTrainingDataset.MaxDelayed;

/**
 * A dataflow pipeline to create the training dataset to predict whether a
 * flight will be delayed by 15 or more minutes.
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
	}

	public static class Flight implements Serializable {
		String date;
		String fromAirport;
		double departureDelay;
		double taxiOutTime;
		double distance;
		double arrivalDelay;
		@Override
		public String toString() {
			return "Flight [date=" + date + ", fromAirport=" + fromAirport + ", departureDelay=" + departureDelay
					+ ", taxiOutTime=" + taxiOutTime + ", distance=" + distance + ", arrivalDelay=" + arrivalDelay
					+ "]";
		}
	}

	@SuppressWarnings("serial")
	public static class SelectFields extends DoFn<String, Flight> {
		@Override
	    public void processElement(ProcessContext c) {
			String line = c.element();
			try {
				String[] fields = line.split(",");
				if (fields[22].length() == 0) {
					return; // delayed/canceled
				}
				// get values
				Flight f = new Flight();
				f.date = fields[0];
				f.fromAirport = fields[8];
				f.departureDelay = Double.parseDouble(fields[15]);
				f.taxiOutTime = Double.parseDouble(fields[16]);
				f.distance = Double.parseDouble(fields[26]);
				f.arrivalDelay = Double.parseDouble(fields[22]);
				c.output(f);
			} catch (Exception e) {
				LOG.warn("Malformed line {" + line + "} skipped", e);
			}
	    }
	}

	@SuppressWarnings("serial")
	public static class MaxDelayed implements SerializableFunction<Iterable<Flight>, Flight> {
		
		@Override
		public Flight apply(Iterable<Flight> flights) {
			Flight maxF = null;
			for (Flight f : flights) {
				if (maxF == null || f.arrivalDelay > maxF.arrivalDelay) {
					maxF = f;
				}
			}
			return maxF;
		}

	}
	
	@SuppressWarnings("serial")
	public static class ToString extends DoFn<Flight, String> {

		@Override
		public void processElement(DoFn<Flight, String>.ProcessContext c) throws Exception {
			Flight f = c.element();
			c.output(f.toString());
		}

	}
	
	public static void main(String[] args) {
		MyOptions options = PipelineOptionsFactory.fromArgs(args).withValidation().as(MyOptions.class);
		Pipeline p = Pipeline.create(options);

		PCollection<String> lines = p.apply(TextIO.Read.named("ReadLines").from(options.getInput()));
		PCollection<Flight> flights = lines.apply(ParDo.of(new SelectFields()));
		PCollection<Flight> maxdelayed = flights.apply(Combine.globally(new MaxDelayed()));
		
		PCollection<String> output = maxdelayed.apply(ParDo.of(new ToString()));
		output.apply(TextIO.Write.named("WriteResult").to("/tmp/output.txt"));
		p.run();
	}
}
