/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.google.cloud.training.dataflowsql;

import org.apache.avro.generic.GenericRecord;
import org.apache.beam.runners.dataflow.DataflowRunner;
import org.apache.beam.runners.dataflow.options.DataflowPipelineOptions;
import org.apache.beam.sdk.Pipeline;
import org.apache.beam.sdk.extensions.sql.SqlTransform;
import org.apache.beam.sdk.extensions.sql.impl.BeamSqlPipelineOptions;
import org.apache.beam.sdk.io.AvroIO;
import org.apache.beam.sdk.io.AvroIO.Parse;
import org.apache.beam.sdk.io.TextIO;
import org.apache.beam.sdk.options.Default;
import org.apache.beam.sdk.options.Description;
import org.apache.beam.sdk.options.PipelineOptionsFactory;
import org.apache.beam.sdk.schemas.Schema;
import org.apache.beam.sdk.transforms.MapElements;
import org.apache.beam.sdk.transforms.SerializableFunction;
import org.apache.beam.sdk.transforms.SimpleFunction;
import org.apache.beam.sdk.transforms.Watch;
import org.apache.beam.sdk.values.PCollection;
import org.apache.beam.sdk.values.Row;
import org.joda.time.Duration;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Example of running SQL on Avro files using Dataflow
 *
 * <p>
 * You should specify the following command-line options: --bucket=<YOUR_BUCKET>
 * 
 * Optionally, you can also provide this option: --streaming --onCloud
 */
public class UpsetsByDay {
	private static final Logger LOG = LoggerFactory.getLogger(UpsetsByDay.class);

	public static interface MyOptions extends DataflowPipelineOptions, BeamSqlPipelineOptions {
		@Description("Bucket for I/O")
		@Default.String("cloud-training-demos-ml")
		String getBucket();

		void setBucket(String s);

		@Description("Run this on the cloud, and not locally?")
		@Default.Boolean(false)
		Boolean isOnCloud();

		void setOnCloud(Boolean b);
	}

	@SuppressWarnings("serial")
	public static void main(String[] args) {
		MyOptions options = PipelineOptionsFactory.fromArgs(args).withValidation().as(MyOptions.class);

		if (options.isOnCloud()) {
			options.setRunner(DataflowRunner.class);
			options.setTempLocation("gs://" + options.getBucket() + "/ncaa/tmp");
		}

		options.setPlannerName("org.apache.beam.sdk.extensions.sql.zetasql.ZetaSQLQueryPlanner");

		Pipeline p = Pipeline.create(options);

		String inFilenamePattern = "gs://" + options.getBucket() + "/ncaa/mbb_*.avro";
		LOG.info("Reading from " + inFilenamePattern);

		// The columns that our query needs (we ignore the other fields)
		Schema schema = Schema.builder().addStringField("day").addStringField("win_seed").addStringField("lose_seed")
				.build();

		// read Avro file(s) and convert to Row
		Parse<Row> avroParser = AvroIO.parseGenericRecords(new SerializableFunction<GenericRecord, Row>() {
			@Override
			public Row apply(GenericRecord record) {
				return Row.withSchema(schema).addValues(record.get("day").toString(), record.get("win_seed").toString(),
						record.get("lose_seed").toString()).build();
			}
		}).from(inFilenamePattern);
		if (options.isStreaming()) {
			avroParser = avroParser.watchForNewFiles(
					// Check for new files every minute
					Duration.standardMinutes(1),
					// Stop watching the file pattern if no new files appear within an hour
					Watch.Growth.afterTimeSinceNewOutput(Duration.standardHours(1)));
		}
		PCollection<Row> games = p.apply("ReadAvro", avroParser).setRowSchema(schema);

		// apply the query; because we haven't done any TUMBLE, the group by is global
		String query = "SELECT day, SUM(IF(win_seed > lose_seed, 1, 0))/COUNT(*) AS upset_ratio "
				+ "FROM PCOLLECTION GROUP BY day ORDER BY upset_ratio DESC";
		PCollection<Row> upsets_by_day = games.apply("sql", SqlTransform.query(query));

		// write output
		String outputPath = "gs://" + options.getBucket() + "/ncaa/upsets_by_day";
		PCollection<String> csvLines = upsets_by_day.apply("WriteCsv",
				MapElements.via(new SimpleFunction<Row, String>() {
					@Override
					public String apply(Row r) {
						String line = r.getString("day") + "," + r.getString("upsets_by_day");
						return line;
					}
				}));
		csvLines.apply(TextIO.write().to(outputPath).withSuffix(".csv"));

		if (options.isStreaming()) {
			p.run();
		} else {
			p.run().waitUntilFinish();
		}
	}
}
