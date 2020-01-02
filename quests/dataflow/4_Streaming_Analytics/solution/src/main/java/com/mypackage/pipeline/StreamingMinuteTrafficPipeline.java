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

import com.google.api.services.bigquery.model.TableFieldSchema;
import com.google.api.services.bigquery.model.TableRow;
import com.google.api.services.bigquery.model.TableSchema;
import com.google.gson.Gson;
import org.apache.beam.sdk.Pipeline;
import org.apache.beam.sdk.PipelineResult;
import org.apache.beam.sdk.io.gcp.bigquery.BigQueryIO;
import org.apache.beam.sdk.io.gcp.pubsub.PubsubIO;
import org.apache.beam.sdk.io.gcp.pubsub.PubsubMessage;
import org.apache.beam.sdk.options.Description;
import org.apache.beam.sdk.options.PipelineOptions;
import org.apache.beam.sdk.options.PipelineOptionsFactory;
import org.apache.beam.sdk.options.StreamingOptions;
import org.apache.beam.sdk.transforms.*;
import org.apache.beam.sdk.transforms.windowing.*;
import org.apache.beam.sdk.values.PCollection;
import org.joda.time.Duration;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.apache.beam.sdk.values.TupleTag;


import java.time.Instant;
import java.util.ArrayList;
import java.util.List;

/**
 * The {@link StreamingMinuteTrafficPipeline} is a sample pipeline which can be used as a base for creating a real
 * Dataflow pipeline.
 *
 * <p><b>Pipeline Requirements</b>
 *
 * <ul>
 * <li>Requirement #1
 * <li>Requirement #2
 * </ul>
 *
 * <p><b>Example Usage</b>
 *
 * <pre>
 * # Set the pipeline vars
 * PROJECT_ID=PROJECT_ID
 * PIPELINE_FOLDER=gs://${PROJECT_ID}/dataflow/pipelines/sample-pipeline
 *
 * # Set the runner
 * RUNNER=DataflowRunner
 *
 * # Build the template
 * mvn compile exec:java \
 * -Dexec.mainClass=com.mypackage.pipeline.StreamingMinuteTrafficPipeline \
 * -Dexec.cleanupDaemonThreads=false \
 * -Dexec.args=" \
 * --project=${PROJECT_ID} \
 * --stagingLocation=${PIPELINE_FOLDER}/staging \
 * --tempLocation=${PIPELINE_FOLDER}/temp \
 * --runner=${RUNNER} \
 * ADDITIONAL PARAMETERS HERE"
 * </pre>
 */
public class StreamingMinuteTrafficPipeline {

    static final TupleTag<CommonLog> parsedMessages = new TupleTag<CommonLog>() {
    };
    static final TupleTag<String> unparsedMessages = new TupleTag<String>() {
    };

    /*
     * The logger to output status messages to.
     */
    private static final Logger LOG = LoggerFactory.getLogger(StreamingMinuteTrafficPipeline.class);

    /**
     * The {@link Options} class provides the custom execution options passed by the executor at the
     * command-line.
     */
    public interface Options extends PipelineOptions, StreamingOptions {
        @Description(
                "The Cloud Pub/Sub topic to consume from.")
        String getInputTopic();

        void setInputTopic(String inputTopic);

        @Description("Window duration length, in minutes")
        Integer getWindowDuration();

        void setWindowDuration(Integer windowDuration);

        @Description(
                "The Cloud BigQuery table name to write raw data to. "
                        + "The name should be in the format of "
                        + "<project-id>:<dataset>.<table-name>."
        )
        String getRawOutputTableName();
        void setRawOutputTableName(String rawOutputTableName);

        @Description(
                "The Cloud BigQuery table name to write aggregated data to. "
                        + "The name should be in the format of "
                        + "<project-id>:<dataset>.<table-name>."
        )
        String getAggregateOutputTableName();
        void setAggregateOutputTableName(String aggregateOutputTableName);

    }

    /**
     * A DoFn which accepts a JSON string and emits a CommonLog
     */
    public static class JsonToCommonLog
            extends DoFn<String, CommonLog> {

        @ProcessElement
        public void processElement(@Element String json,
                                   OutputReceiver<CommonLog> receiver) {
            // Use Expose() annotation, so that Gson does not expect processing_timestamp field
            Gson gson = new Gson();
            CommonLog commonLog = gson.fromJson(json, CommonLog.class);
            receiver.output(commonLog);
        }
    }


    /**
     * A DoFn which accepts a JSON string outputs a instance of TableRow
     */
    static class LongToTableRowFn extends DoFn<Long, TableRow> {

        @ProcessElement
        public void processElement(@Element Long l,
                                   OutputReceiver<TableRow> r, IntervalWindow window)  throws Exception {
            Instant i = Instant.ofEpochMilli(window.end().getMillis());
            TableRow tableRow = new TableRow();
            tableRow.set("window_end", i.toString());
            tableRow.set("pageviews", l.intValue());
            r.output(tableRow);
        }
    }

    /**
     * The main entry-point for pipeline execution. This method will start the pipeline but will not
     * wait for it's execution to finish. If blocking execution is required, use the {@link
     * StreamingMinuteTrafficPipeline#run(Options)} method to start the pipeline and invoke
     * {@code result.waitUntilFinish()} on the {@link PipelineResult}.
     *
     * @param args The command-line args passed by the executor.
     */
    public static void main(String[] args) {
        PipelineOptionsFactory.register(Options.class);
        Options options = PipelineOptionsFactory.fromArgs(args).as(Options.class);
        options.setStreaming(true);
        run(options);
    }

    /**
     * Runs the pipeline to completion with the specified options. This method does not wait until the
     * pipeline is finished before returning. Invoke {@code result.waitUntilFinish()} on the result
     * object to block until the pipeline is finished running if blocking programmatic execution is
     * required.
     *
     * @param options The execution options.
     * @return The pipeline result.
     */
    public static PipelineResult run(Options options) {

        // Create the pipeline
        Pipeline pipeline = Pipeline.create(options);
        options.setJobName("streaming-minute-traffic-pipeline-" + System.currentTimeMillis());

        List<TableFieldSchema> rawFields = new ArrayList<>();
        rawFields.add(new TableFieldSchema().setName("user_id").setType("STRING"));
        rawFields.add(new TableFieldSchema().setName("event_timestamp").setType("TIMESTAMP"));
        rawFields.add(new TableFieldSchema().setName("processing_timestamp").setType("TIMESTAMP"));
        TableSchema rawSchema = new TableSchema().setFields(rawFields);

        List<TableFieldSchema> aggregateFields = new ArrayList<>();
        aggregateFields.add(new TableFieldSchema().setName("window_end").setType("TIMESTAMP"));
        aggregateFields.add(new TableFieldSchema().setName("pageviews").setType("INTEGER"));
        TableSchema aggregateSchema = new TableSchema().setFields(aggregateFields);

        LOG.info("Building pipeline...");

        // Read PubsubMessages, parse them into CommonLogs
        // Add in a field representing processing time
        PCollection<CommonLog> commonLogs =
                pipeline.apply(
                        "ReadPubSubMessages",
                        PubsubIO.readStrings()
                                // Retrieve timestamp information from Pubsub Message attributes
                                .withTimestampAttribute("timestamp")
                                .fromTopic(options.getInputTopic()))
                        .apply("ConvertPubsubMessageToCommonLog", ParDo.of(new JsonToCommonLog()));

        // Convert CommonLogs to format for raw table, dropping everything except for timestamps
        // Then write to BigQuery
        commonLogs
                .apply("CommonLogToRawTableRow",
                        ParDo.of(new DoFn<CommonLog, TableRow>() {
                            @ProcessElement
                            public void processElement(@Element CommonLog commonLog,
                                                       OutputReceiver<TableRow> r) {
                                TableRow tableRow = new TableRow();
                                tableRow.set("user_id", commonLog.user_id);
                                tableRow.set("event_timestamp", commonLog.timestamp);
                                tableRow.set("processing_timestamp", Instant.now().toString());
                                r.output(tableRow);
                            }
                        }))
                .apply("WriteRawDataToBigQuery",
                        BigQueryIO
                                .writeTableRows()
                                .to(options.getRawOutputTableName())
                                .withSchema(rawSchema)
                                .withWriteDisposition(BigQueryIO.Write.WriteDisposition.WRITE_APPEND)
                                .withCreateDisposition(BigQueryIO.Write.CreateDisposition.CREATE_IF_NEEDED));
        // Window events, then count the number of events within each window
        // Before finally converting to TableRow and writing to BigQuery
        commonLogs
                .apply("WindowCommonLogs",
                        Window.into(
                                FixedWindows.of(
                                        Duration.standardMinutes(options.getWindowDuration()))))
                .apply("CountEventsPerWindow",
                        Combine.globally(Count.<CommonLog>combineFn()).withoutDefaults())
                .apply("ConvertLongToTableRow",
                        ParDo.of(new LongToTableRowFn()))
                .apply("WriteAggregatedDataToBigQuery",
                        BigQueryIO
                                .writeTableRows()
                                .to(options.getAggregateOutputTableName())
                                .withSchema(aggregateSchema)
                                .withWriteDisposition(BigQueryIO.Write.WriteDisposition.WRITE_APPEND)
                                .withCreateDisposition(BigQueryIO.Write.CreateDisposition.CREATE_IF_NEEDED));

        return pipeline.run();
    }
}
