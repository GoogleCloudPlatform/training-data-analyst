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

package com.google.cloud.training.dataanalyst.javahelp;

import java.time.Instant;
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
import org.apache.beam.sdk.transforms.ParDo;
import org.apache.beam.sdk.transforms.Sum;
import org.apache.beam.sdk.transforms.windowing.SlidingWindows;
import org.apache.beam.sdk.transforms.windowing.Window;
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
public class StreamDemoConsumer {

	public static interface MyOptions extends DataflowPipelineOptions {
		@Description("Output BigQuery table <project_id>:<dataset_id>.<table_id>")
		@Default.String("cloud-training-demos:demos.streamdemo")
		String getOutput();

		void setOutput(String s);

		@Description("Input topic")
		@Default.String("projects/cloud-training-demos/topics/streamdemo")
		String getInput();
		
		void setInput(String s);
	}

	@SuppressWarnings("serial")
	public static void main(String[] args) {
		MyOptions options = PipelineOptionsFactory.fromArgs(args).withValidation().as(MyOptions.class);
		options.setStreaming(true);
		Pipeline p = Pipeline.create(options);

		String topic = options.getInput();
		String output = options.getOutput();

		// Build the table schema for the output table.
		List<TableFieldSchema> fields = new ArrayList<>();
		fields.add(new TableFieldSchema().setName("timestamp").setType("TIMESTAMP"));
		fields.add(new TableFieldSchema().setName("num_words").setType("INTEGER"));
		TableSchema schema = new TableSchema().setFields(fields);

		p //
				.apply("GetMessages", PubsubIO.readStrings().fromTopic(topic)) //
				.apply("window",
						Window.into(SlidingWindows//
								.of(Duration.standardMinutes(2))//
								.every(Duration.standardSeconds(30)))) //
				.apply("WordsPerLine", ParDo.of(new DoFn<String, Integer>() {
					@ProcessElement
					public void processElement(ProcessContext c) throws Exception {
						String line = c.element();
						c.output(line.split(" ").length);
					}
				}))//
				.apply("WordsInTimeWindow", Sum.integersGlobally().withoutDefaults()) //
				.apply("ToBQRow", ParDo.of(new DoFn<Integer, TableRow>() {
					@ProcessElement
					public void processElement(ProcessContext c) throws Exception {
						TableRow row = new TableRow();
						row.set("timestamp", Instant.now().toString());
						row.set("num_words", c.element());
						c.output(row);
					}
				})) //
				.apply(BigQueryIO.writeTableRows().to(output)//
						.withSchema(schema)//
						.withWriteDisposition(BigQueryIO.Write.WriteDisposition.WRITE_APPEND)
						.withCreateDisposition(BigQueryIO.Write.CreateDisposition.CREATE_IF_NEEDED));

		p.run();
	}
}
