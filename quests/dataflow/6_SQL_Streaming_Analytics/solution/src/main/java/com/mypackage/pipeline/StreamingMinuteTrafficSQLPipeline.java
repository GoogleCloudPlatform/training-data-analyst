/*
 * Copyright (C) 2018 Google Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */


package com.mypackage.pipeline;

import com.google.gson.Gson;
import org.apache.beam.runners.dataflow.options.DataflowPipelineOptions;
import org.apache.beam.sdk.Pipeline;
import org.apache.beam.sdk.PipelineResult;
import org.apache.beam.sdk.extensions.sql.SqlTransform;
import org.apache.beam.sdk.extensions.sql.impl.BeamSqlPipelineOptions;
import org.apache.beam.sdk.io.gcp.bigquery.BigQueryIO;
import org.apache.beam.sdk.io.gcp.pubsub.PubsubIO;
import org.apache.beam.sdk.options.Description;
import org.apache.beam.sdk.options.PipelineOptionsFactory;
import org.apache.beam.sdk.schemas.Schema;
import org.apache.beam.sdk.schemas.Schema.FieldType;
import org.apache.beam.sdk.schemas.transforms.AddFields;
import org.apache.beam.sdk.transforms.MapElements;
import org.apache.beam.sdk.transforms.ParDo;
import org.apache.beam.sdk.transforms.SimpleFunction;
import org.apache.beam.sdk.transforms.WithTimestamps;
import org.apache.beam.sdk.transforms.*;
import org.apache.beam.sdk.values.PCollection;
import org.apache.beam.sdk.values.Row;
import org.joda.time.DateTime;
import org.joda.time.Instant;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;


public class StreamingMinuteTrafficSQLPipeline {

    /**
     * The logger to output status messages to.
     */
    private static final Logger LOG = LoggerFactory.getLogger(StreamingMinuteTrafficSQLPipeline.class);

    /**
     * The {@link Options} class provides the custom execution options passed by the
     * executor at the command-line.
     */
    public interface Options extends DataflowPipelineOptions, BeamSqlPipelineOptions {
        @Description("Input topic name")
        String getInputTopic();
        void setInputTopic(String inputTopic);

        @Description("BigQuery table name")
        String getTableName();
        void setTableName(String tableName);
    }

    /**
     * The main entry-point for pipeline execution. This method will start the
     * pipeline but will not wait for it's execution to finish. If blocking
     * execution is required, use the {@link StreamingMinuteTrafficSQLPipeline#run(Options)} method to
     * start the pipeline and invoke {@code result.waitUntilFinish()} on the
     * {@link PipelineResult}.
     *
     * @param args The command-line args passed by the executor.
     */
    public static void main(String[] args) {
        Options options = PipelineOptionsFactory.fromArgs(args).withValidation().as(Options.class);
        options.setPlannerName("org.apache.beam.sdk.extensions.sql.zetasql.ZetaSQLQueryPlanner");
        run(options);
    }


    /**
     * A DoFn acccepting Json and outputing CommonLog with Beam Schema
     */
    static class JsonToCommonLog extends DoFn<String, CommonLog> {

        @ProcessElement
        public void processElement(@Element String json, OutputReceiver<CommonLog> r) throws Exception {
            Gson gson = new Gson();
            CommonLog commonLog = gson.fromJson(json, CommonLog.class);
            r.output(commonLog);
        }
    }

    /**
     * A Beam schema for counting pageviews per minute
     */

    public static final Schema jodaCommonLogSchema = Schema.builder()
            .addStringField("user_id")
            .addStringField("ip")
            .addDoubleField("lat")
            .addDoubleField("lng")
            .addStringField("timestamp")
            .addStringField("http_request")
            .addStringField("user_agent")
            .addInt64Field("http_response")
            .addInt64Field("num_bytes")
            .addDateTimeField("timestamp_joda")
            .build();

    /**
     * Runs the pipeline to completion with the specified options. This method does
     * not wait until the pipeline is finished before returning. Invoke
     * {@code result.waitUntilFinish()} on the result object to block until the
     * pipeline is finished running if blocking programmatic execution is required.
     *
     * @param options The execution options.
     * @return The pipeline result.
     */
    public static PipelineResult run(Options options) {

        // Create the pipeline
        Pipeline pipeline = Pipeline.create(options);
        options.setJobName("streaming-minute-traffic-sql-pipeline-" + System.currentTimeMillis());

        /*
         * Steps:
         * 1) Read something
         * 2) Transform something
         * 3) Write something
         */

        pipeline
                // Read in lines from PubSub and Parse to CommonLog
                .apply("ReadMessage", PubsubIO.readStrings()
                    .withTimestampAttribute("timestamp")
                    .fromTopic(options.getInputTopic()))

                .apply("ParseJson", ParDo.of(new JsonToCommonLog()))

                // Add new DATETIME field to CommonLog, converting to a Row, then populate new row with Joda DateTime
                .apply("AddDateTimeField", AddFields.<CommonLog>create().field("timestamp_joda", FieldType.DATETIME))
                .apply("AddDateTimeValue", MapElements.via(new SimpleFunction<Row, Row>() {
                    @Override
                    public Row apply(Row row) {
                        DateTime dateTime = new DateTime(row.getString("timestamp"));
                        return Row.withSchema(row.getSchema())
                                .addValues(
                                        row.getString("user_id"),
                                        row.getString("ip"),
                                        row.getDouble("lat"),
                                        row.getDouble("lng"),
                                        row.getString("timestamp"),
                                        row.getString("http_request"),
                                        row.getString("user_agent"),
                                        row.getInt64("http_response"),
                                        row.getInt64("num_bytes"),
                                        dateTime)
                                .build();
                    }
                })).setRowSchema(jodaCommonLogSchema)

                // Apply a SqlTransform.query(QUERY_TEXT) to count window and count total page views, write to BQ
                .apply("WindowedAggregateQuery", SqlTransform.query(
                        "SELECT COUNT(*) AS pageviews, tr.window_start AS minute FROM TUMBLE( ( SELECT * FROM " +
                                "PCOLLECTION ) , DESCRIPTOR(timestamp_joda), \"INTERVAL 1 MINUTE\") AS tr GROUP " +
                                "BY tr.window_start"))
                .apply("WriteToBQ",
                        BigQueryIO.<Row>write().to(options.getTableName()).useBeamSchema()
                                .withWriteDisposition(BigQueryIO.Write.WriteDisposition.WRITE_APPEND)
                                .withCreateDisposition(BigQueryIO.Write.CreateDisposition.CREATE_IF_NEEDED));




        LOG.info("Building pipeline...");

        return pipeline.run();
    }
}