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

import java.util.ArrayList;
import java.util.List;

import org.joda.time.Duration;

import com.google.api.services.bigquery.model.TableFieldSchema;
import com.google.api.services.bigquery.model.TableRow;
import com.google.api.services.bigquery.model.TableSchema;
import com.google.cloud.dataflow.sdk.Pipeline;
import com.google.cloud.dataflow.sdk.coders.AvroCoder;
import com.google.cloud.dataflow.sdk.coders.DefaultCoder;
import com.google.cloud.dataflow.sdk.io.BigQueryIO;
import com.google.cloud.dataflow.sdk.io.PubsubIO;
import com.google.cloud.dataflow.sdk.options.DataflowPipelineOptions;
import com.google.cloud.dataflow.sdk.options.Default;
import com.google.cloud.dataflow.sdk.options.Description;
import com.google.cloud.dataflow.sdk.options.PipelineOptionsFactory;
import com.google.cloud.dataflow.sdk.transforms.DoFn;
import com.google.cloud.dataflow.sdk.transforms.Max;
import com.google.cloud.dataflow.sdk.transforms.Mean;
import com.google.cloud.dataflow.sdk.transforms.ParDo;
import com.google.cloud.dataflow.sdk.transforms.join.CoGbkResult;
import com.google.cloud.dataflow.sdk.transforms.join.CoGroupByKey;
import com.google.cloud.dataflow.sdk.transforms.join.KeyedPCollectionTuple;
import com.google.cloud.dataflow.sdk.transforms.windowing.SlidingWindows;
import com.google.cloud.dataflow.sdk.transforms.windowing.Window;
import com.google.cloud.dataflow.sdk.values.KV;
import com.google.cloud.dataflow.sdk.values.PCollection;
import com.google.cloud.dataflow.sdk.values.TupleTag;

/**
 * A dataflow pipeline that listens to a PubSub topic and writes out aggregates
 * on windows to BigQuery
 * 
 * @author vlakshmanan
 *
 */
@SuppressWarnings("serial")
public class AverageDelayPipeline {

	public static interface MyOptions extends DataflowPipelineOptions {
		@Description("Over how long a time period should we average? (in minutes)")
		@Default.Double(15.0)
		Double getAveragingInterval();

		void setAveragingInterval(Double d);

		@Description("Simulation speedup factor if applicable")
		@Default.Double(1.0)
		Double getSpeedupFactor();

		void setSpeedupFactor(Double d);
	}
	
	public static void main(String[] args) {
		MyOptions options = PipelineOptionsFactory.fromArgs(args).withValidation().as(MyOptions.class);
		options.setStreaming(true);
		Pipeline p = Pipeline.create(options);

		// output
		String outputTable = options.getProject() + ':' + "flights.streaming_delays";
		TableSchema schema = createSchema(
				"airport:string,latitude:float,longitude:float,timestamp:timestamp,dep_delay:float,arr_delay:float");

		// compute moving averages
		final WindowStats arr = movingAverageOf(options, p, "arrived");
		//final WindowStats dep = movingAverageOf(options, p, "departed");
		
		// make them local variables, otherwise Java tries to serialize them
		final PCollection<KV<Airport, Double>> arr_delay = arr.delay;
		final PCollection<KV<Airport, String>> arr_timestamp = arr.timestamp;
		//final PCollection<KV<Airport, Double>> dep_delay = dep.delay;
		//final PCollection<KV<Airport, String>> dep_timestamp = dep.timestamp;
		final TupleTag<Double> arr_delayTag = new TupleTag<Double>();
		final TupleTag<String> arr_tsTag = new TupleTag<String>();
		//final TupleTag<Double> dep_delayTag = new TupleTag<Double>();
		//final TupleTag<String> dep_tsTag = new TupleTag<String>();
		
//		// join
//		KeyedPCollectionTuple //
//				.of(arr_delayTag, arr_delay) //
//				//.and(dep_delayTag, dep_delay) //
//				.and(arr_tsTag, arr_timestamp) //
//				//.and(dep_tsTag, dep_timestamp) //
//				.apply("cogroup", CoGroupByKey.<Airport> create()) //
//				.apply("join_delays", ParDo.of(new DoFn<KV<Airport, CoGbkResult>, Airport>() {
//
//					@Override
//					public void processElement(ProcessContext c) throws Exception {
//						KV<Airport, CoGbkResult> e = c.element();
//						Airport airport = e.getKey();
//						Double arrDelay = e.getValue().getOnly(arr_delayTag, new Double(-999));
//						//Double depDelay = e.getValue().getOnly(dep_delayTag, new Double(-999));
//						String arrTs = e.getValue().getOnly(arr_tsTag, "");
//						//String depTs = e.getValue().getOnly(dep_tsTag, "");
//						//String timestamp = (arrTs.compareTo(depTs) > 0)? arrTs : depTs; // latest
//						//c.output(new Airport(airport, arrDelay, depDelay, timestamp));
//						c.output(new Airport(airport, arrDelay, arrDelay, arrTs));
//					}
//
//				}))//
		
		arr_delay.apply(ParDo.of(new DoFn<KV<Airport, Double>, Airport>() {
			public void processElement(ProcessContext c) throws Exception {
				Airport airport = c.element().getKey();
				Double arrDelay = c.element().getValue();
				c.output(new Airport(airport, arrDelay, arrDelay, "2015-05-01 00:00:00 UTC"));
			}
		}))//
				.apply("toBQRow", ParDo.of(new DoFn<Airport, TableRow>() {
					@Override
					public void processElement(ProcessContext c) throws Exception {
						Airport airport = c.element();
						TableRow row = new TableRow();
						row.set("timestamp", airport.timestamp);
						row.set("airport", airport.airport);
						row.set("latitude", airport.latitude);
						row.set("longitude", airport.longitude);
						row.set("dep_delay", airport.dep_delay);
						row.set("arr_delay", airport.arr_delay);
						c.output(row);
					}
				}))//
				.apply("write_to_bq",
						BigQueryIO.Write.to(outputTable) //
								.withSchema(schema)//
								.withCreateDisposition(BigQueryIO.Write.CreateDisposition.CREATE_IF_NEEDED));

		p.run();
	}

	@DefaultCoder(AvroCoder.class)
	public static class Airport implements Comparable<Airport> {
		String airport; // the only field used in comparisons
		double latitude;
		double longitude;
		double arr_delay;
		double dep_delay;
		String timestamp;

		public Airport(String line, String event) {
			int nameFieldNumber, latFieldNumber, lonFieldNumber, delayFieldNumber, timeFieldNumber;
			if (event.equals("arrived")) {
				nameFieldNumber = 13; // DEST
				latFieldNumber = 31; // ARR_AIRPORT_LAT
				delayFieldNumber = 23; // ARR_DELAY
				timeFieldNumber = 22; // ARR_TIME
			} else {
				nameFieldNumber = 9; // ORIGIN
				latFieldNumber = 28; // DEP_AIRPORT_LAT
				delayFieldNumber = 16; // DEP_DELAY
				timeFieldNumber = 15; // DEP_TIME
			}
			lonFieldNumber = latFieldNumber + 1;

			String[] fields = line.split(",");	
			this.airport = fields[nameFieldNumber - 1];
			this.latitude = Double.parseDouble(fields[latFieldNumber - 1]);
			this.longitude = Double.parseDouble(fields[lonFieldNumber - 1]);
			this.arr_delay = this.dep_delay = Double.parseDouble(fields[delayFieldNumber - 1]);
			this.timestamp = fields[timeFieldNumber - 1];
		}

		public Airport(Airport other, Double arrDelay, Double depDelay, String timestamp) {
			this.airport = other.airport;
			this.latitude = other.latitude;
			this.longitude = other.longitude;
			this.arr_delay = arrDelay;
			this.dep_delay = depDelay;
			this.timestamp = timestamp;
		}

		public Airport() {
			// for Avro only
		}
		
		@Override
		public int hashCode() {
			final int prime = 31;
			int result = 1;
			result = prime * result + ((airport == null) ? 0 : airport.hashCode());
			return result;
		}

		@Override
		public boolean equals(Object obj) {
			if (this == obj)
				return true;
			if (obj == null)
				return false;
			if (getClass() != obj.getClass())
				return false;
			Airport other = (Airport) obj;
			if (airport == null) {
				if (other.airport != null)
					return false;
			} else if (!airport.equals(other.airport))
				return false;
			return true;
		}

		@Override
		public int compareTo(Airport other) {
			return this.airport.compareTo(other.airport);
		}
	}

	public static class WindowStats {
		PCollection<KV<Airport, Double>> delay;
		PCollection<KV<Airport, String>> timestamp;
	}

	private static WindowStats movingAverageOf(MyOptions options, Pipeline p, String event) {
		// if we need to average over 60 minutes and speedup is 30x
		// then we need to average over 2 minutes of sped-up stream
		Duration averagingInterval = Duration
				.millis(Math.round(1000 * 60 * (options.getAveragingInterval() / options.getSpeedupFactor())));
		Duration averagingFrequency = averagingInterval.dividedBy(2); // 2 times in window

		System.out.println("Averaging interval = " + averagingInterval);
		System.out.println("Averaging freq = " + averagingFrequency);
		
		String topic = "projects/" + options.getProject() + "/topics/" + event;
		PCollection<Airport> airports = p //
				.apply(event + ":read", PubsubIO.Read.topic(topic)) //
				.apply(event + ":window",
						Window.into(SlidingWindows//
								.of(averagingInterval)//
								.every(averagingFrequency))) //
				.apply(event + ":parse", ParDo.of(new DoFn<String, Airport>() {
					@Override
					public void processElement(ProcessContext c) throws Exception {
						try {
							Airport airport = new Airport(c.element(), event);
							c.output(airport);
						} catch (NumberFormatException e) {
							// ignore errors about empty delay fields ...
						}
					}
				}));
		
		WindowStats stats = new WindowStats();
		stats.delay = airports //
				.apply(event + ":airportdelay", ParDo.of(new DoFn<Airport, KV<Airport, Double>>() {
					@Override
					public void processElement(ProcessContext c) throws Exception {
						Airport airport = c.element();
						c.output(KV.of(airport, airport.arr_delay)); // same as dep_delay
					}
				}))//
				.apply(event + ":avgdelay", Mean.perKey());
		
		stats.timestamp = airports //
				.apply(event + ":timestamps", ParDo.of(new DoFn<Airport, KV<Airport, String>>() {
					@Override
					public void processElement(ProcessContext c) throws Exception {
						Airport airport = c.element();
						c.output(KV.of(airport, airport.timestamp));
					}
				}))//
				.apply(event + ":lastTimeStamp", Max.perKey());
		
		return stats;
	}

	private static TableSchema createSchema(String schemaText) {
		List<TableFieldSchema> fields = new ArrayList<>();
		for (String desc : schemaText.split(",")) {
			String[] pieces = desc.split(":");
			fields.add(new TableFieldSchema().setName(pieces[0]).setType(pieces[1]));
		}
		TableSchema schema = new TableSchema().setFields(fields);
		return schema;
	}
}
