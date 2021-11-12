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

import org.apache.beam.runners.dataflow.options.DataflowPipelineOptions;
import org.apache.beam.sdk.Pipeline;
import org.apache.beam.sdk.io.gcp.bigquery.BigQueryIO;
import org.apache.beam.sdk.io.gcp.pubsub.PubsubIO;
import org.apache.beam.sdk.options.Default;
import org.apache.beam.sdk.options.Description;
import org.apache.beam.sdk.options.PipelineOptionsFactory;
import org.apache.beam.sdk.transforms.DoFn;
import org.apache.beam.sdk.transforms.Max;
import org.apache.beam.sdk.transforms.Mean;
import org.apache.beam.sdk.transforms.ParDo;
import org.apache.beam.sdk.transforms.Sum;
import org.apache.beam.sdk.transforms.join.CoGbkResult;
import org.apache.beam.sdk.transforms.join.CoGroupByKey;
import org.apache.beam.sdk.transforms.join.KeyedPCollectionTuple;
import org.apache.beam.sdk.transforms.windowing.SlidingWindows;
import org.apache.beam.sdk.transforms.windowing.Window;
import org.apache.beam.sdk.values.KV;
import org.apache.beam.sdk.values.PCollection;
import org.apache.beam.sdk.values.TupleTag;
import org.joda.time.Duration;

import com.google.api.services.bigquery.model.TableFieldSchema;
import com.google.api.services.bigquery.model.TableRow;
import com.google.api.services.bigquery.model.TableSchema;

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
		MyOptions options = PipelineOptionsFactory.fromArgs(args).//
				withValidation().as(MyOptions.class);
		options.setStreaming(true);
		Pipeline p = Pipeline.create(options);

		// output
		String outputTable = options.getProject() + ':' + "flights.streaming_delays";
		TableSchema schema = createSchema("airport:string,latitude:float,longitude:float,"
				+ "timestamp:timestamp,dep_delay:float,arr_delay:float,num_flights:integer");

		// compute moving averages
		final WindowStats arr = movingAverageOf(options, p, "arrived");
		final WindowStats dep = movingAverageOf(options, p, "departed");
		
		// make them local variables, otherwise Java tries to serialize them into the anonymous class
		final PCollection<KV<Airport, Double>> arr_delay = arr.delay;
		final PCollection<KV<Airport, String>> arr_timestamp = arr.timestamp;
		final PCollection<KV<Airport, Integer>> arr_num_flights = arr.num_flights;
		final PCollection<KV<Airport, Double>> dep_delay = dep.delay;
		final PCollection<KV<Airport, String>> dep_timestamp = dep.timestamp;
		final PCollection<KV<Airport, Integer>> dep_num_flights = dep.num_flights;
		final TupleTag<Double> arr_delayTag = new TupleTag<Double>();
		final TupleTag<String> arr_tsTag = new TupleTag<String>();
		final TupleTag<Integer> arr_nfTag = new TupleTag<Integer>();
		final TupleTag<Double> dep_delayTag = new TupleTag<Double>();
		final TupleTag<String> dep_tsTag = new TupleTag<String>();
		final TupleTag<Integer> dep_nfTag = new TupleTag<Integer>();
		
		// join
		KeyedPCollectionTuple //
				.of(arr_delayTag, arr_delay) //
				.and(dep_delayTag, dep_delay) //
				.and(arr_tsTag, arr_timestamp) //
				.and(dep_tsTag, dep_timestamp) //
				.and(arr_nfTag, arr_num_flights) //
				.and(dep_nfTag, dep_num_flights) //
				.apply("airport:cogroup", CoGroupByKey.<Airport> create()) //
				.apply("airport:stats", ParDo.of(new DoFn<KV<Airport, CoGbkResult>, AirportStats>() {

					@ProcessElement
					public void processElement(ProcessContext c) throws Exception {
						KV<Airport, CoGbkResult> e = c.element();
						Airport airport = e.getKey();
						Double arrDelay = e.getValue().getOnly(arr_delayTag, new Double(-999));
						Double depDelay = e.getValue().getOnly(dep_delayTag, new Double(-999));
						String arrTs = e.getValue().getOnly(arr_tsTag, "");
						String depTs = e.getValue().getOnly(dep_tsTag, "");
						String timestamp = (arrTs.compareTo(depTs) > 0)? arrTs : depTs; // latest
						int num_flights = //
								e.getValue().getOnly(arr_nfTag, new Integer(0)).intValue() + //
								e.getValue().getOnly(dep_nfTag, new Integer(0)).intValue();
						c.output(new AirportStats(airport, arrDelay, depDelay, timestamp, num_flights));
					}

				}))//
				.apply("airport:to_BQrow", ParDo.of(new DoFn<AirportStats, TableRow>() {
					@ProcessElement
					public void processElement(ProcessContext c) throws Exception {
						AirportStats stats = c.element();
						TableRow row = new TableRow();
						row.set("timestamp", stats.timestamp);
						row.set("airport", stats.airport.name);
						row.set("latitude", stats.airport.latitude);
						row.set("longitude", stats.airport.longitude);
						if (stats.dep_delay > -998)
							row.set("dep_delay", stats.dep_delay); // else null
						if (stats.arr_delay > -998)
							row.set("arr_delay", stats.arr_delay); // else null
						row.set("num_flights", stats.num_flights);
						c.output(row);
					}
				}))//
				.apply("airport:write_toBQ",
						BigQueryIO.writeTableRows().to(outputTable) //
								.withSchema(schema)//
								.withWriteDisposition(BigQueryIO.Write.WriteDisposition.WRITE_APPEND)
								.withCreateDisposition(BigQueryIO.Write.CreateDisposition.CREATE_IF_NEEDED));

		p.run();
	}

	public static class WindowStats {
		PCollection<KV<Airport, Double>> delay;
		PCollection<KV<Airport, String>> timestamp;
		PCollection<KV<Airport, Integer>> num_flights;
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
		final FieldNumberLookup eventType = FieldNumberLookup.create(event);
		PCollection<Flight> flights = p //
				.apply(event + ":read", //
						PubsubIO.readStrings().fromTopic(topic)) //
				.apply(event + ":window",
						Window.into(SlidingWindows//
								.of(averagingInterval)//
								.every(averagingFrequency))) //
				.apply(event + ":parse", ParDo.of(new DoFn<String, Flight>() {
					@ProcessElement
					public void processElement(ProcessContext c) throws Exception {
						try {
							String line = c.element();
							Flight f = new Flight(line.split(","), eventType);
							c.output(f);
						} catch (NumberFormatException e) {
							// ignore errors about empty delay fields ...
						}
					}
				}));
		
		WindowStats stats = new WindowStats();
		stats.delay = flights //
				.apply(event + ":airportdelay", ParDo.of(new DoFn<Flight, KV<Airport, Double>>() {
					@ProcessElement
					public void processElement(ProcessContext c) throws Exception {
						Flight stats = c.element();
						c.output(KV.of(stats.airport, stats.delay)); // delay at airport
					}
				}))//
				.apply(event + ":avgdelay", Mean.perKey());
		
		stats.timestamp = flights //
				.apply(event + ":timestamps", ParDo.of(new DoFn<Flight, KV<Airport, String>>() {
					@ProcessElement
					public void processElement(ProcessContext c) throws Exception {
						Flight stats = c.element();
						c.output(KV.of(stats.airport, stats.timestamp));
					}
				}))//
				.apply(event + ":lastTimeStamp", Max.perKey());
		
		stats.num_flights = flights //
				.apply(event + ":numflights", ParDo.of(new DoFn<Flight, KV<Airport, Integer>>() {
					@ProcessElement
					public void processElement(ProcessContext c) throws Exception {
						Flight stats = c.element();
						c.output(KV.of(stats.airport, 1));
					}
				}))//
				.apply(event + ":total", Sum.integersPerKey());
		
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
