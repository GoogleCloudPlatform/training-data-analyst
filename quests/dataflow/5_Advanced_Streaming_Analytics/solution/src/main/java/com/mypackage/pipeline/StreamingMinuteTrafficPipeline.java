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
import com.google.gson.JsonSyntaxException;
import org.apache.beam.sdk.Pipeline;
import org.apache.beam.sdk.PipelineResult;
import org.apache.beam.sdk.io.TextIO;
import org.apache.beam.sdk.io.gcp.bigquery.BigQueryIO;
import org.apache.beam.sdk.io.gcp.bigquery.WriteResult;
import org.apache.beam.sdk.io.gcp.pubsub.PubsubIO;
import org.apache.beam.sdk.options.Description;
import org.apache.beam.sdk.options.PipelineOptions;
import org.apache.beam.sdk.options.PipelineOptionsFactory;
import org.apache.beam.sdk.options.StreamingOptions;
import org.apache.beam.sdk.transforms.*;
import org.apache.beam.sdk.transforms.windowing.*;
import org.apache.beam.sdk.values.PCollection;
import org.apache.beam.sdk.values.PCollectionTuple;
import org.apache.beam.sdk.values.TupleTagList;
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

        @Description("Window allowed lateness, in days")
        Integer getAllowedLateness();

        void setAllowedLateness(Integer allowedLateness);

        @Description(
                "The Cloud BigQuery table name to write to. "
                        + "The name should be in the format of "
                        + "<project-id>:<dataset>.<table-name>."
        )
        String getOutputTableName();

        void setOutputTableName(String outputTableName);

        @Description(
                "The Cloud Storage bucket used for writing "
                        + "unparseable Pubsub Messages."
        )
        String getDeadletterBucket();

        void setDeadletterBucket(String deadletterBucket);
    }

    public static class PubsubMessageToCommonLog
            extends PTransform<PCollection<String>, PCollectionTuple> {

        @Override
        public PCollectionTuple expand(PCollection<String> input) {
            return input
                    .apply(
                            "JsonToCommonLog",
                            ParDo.of(new DoFn<String, CommonLog>() {
                                         @ProcessElement
                                         public void processElement(ProcessContext context) {
                                             String json = context.element();
                                             Gson gson = new Gson();
                                             try {
                                                 CommonLog commonLog = gson.fromJson(json, CommonLog.class);
                                                 context.output(parsedMessages, commonLog);
                                             } catch (JsonSyntaxException e) {
                                                 context.output(unparsedMessages, json);
                                             }
                                         }
                                     })
                            .withOutputTags(parsedMessages, TupleTagList.of(unparsedMessages)));
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
            tableRow.set("window-end", i.toString());
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

        List<TableFieldSchema> fields = new ArrayList<>();
        fields.add(new TableFieldSchema().setName("window-end").setType("TIMESTAMP"));
        fields.add(new TableFieldSchema().setName("pageviews").setType("INTEGER"));
        TableSchema schema = new TableSchema().setFields(fields);

        /*
         * Steps:
         *  1) Read something
         *  2) Transform something
         *  3) Write something
         */
        // Pipeline code goes here
        LOG.info("Building pipeline...");

        PCollectionTuple transformOut =
                pipeline.apply(
                        "ReadPubSubMessages",
                        PubsubIO.readStrings()
                                // Retrieve timestamp information from Pubsub Message attributes
                                .withTimestampAttribute("timestamp")
                                .fromTopic(options.getInputTopic()))
                        .apply("ConvertMessageToCommonLog", new PubsubMessageToCommonLog());

        // Write parsed messages to BigQuery
        transformOut
                // Retrieve parsed messages
                .get(parsedMessages)
                .apply("WindowByMinute",
                        Window.<CommonLog>into(FixedWindows
                                .of(Duration.standardMinutes(options.getWindowDuration())))
                                .withAllowedLateness(Duration.standardDays(options.getAllowedLateness()))
                                .triggering(
                                        AfterWatermark.pastEndOfWindow()
                                                .withLateFirings(AfterPane.elementCountAtLeast(1)))
                                .accumulatingFiredPanes())
                .apply("CountTraffic", Combine.globally(Count.<CommonLog>combineFn()).withoutDefaults())
                // Convert this count into a TableRow
                .apply("LongToTableRow", ParDo.of(new LongToTableRowFn()))
                .apply(
                        "WriteSuccessfulRecords",
                        BigQueryIO.writeTableRows()
                                .to(options.getOutputTableName())
                                .withSchema(schema)
                                .withWriteDisposition(BigQueryIO.Write.WriteDisposition.WRITE_APPEND)
                                .withCreateDisposition(BigQueryIO.Write.CreateDisposition.CREATE_IF_NEEDED));

        // Write unparsed messages to Cloud Storage
        transformOut
                // Retrieve unparsed messages
                .get(unparsedMessages)
                .apply("FireEvery10s",
                        Window.<String>configure()
                                .triggering(AfterProcessingTime.pastFirstElementInPane()
                                        .plusDelayOf(Duration.standardSeconds(10)))
                                .discardingFiredPanes())
                .apply(
                        "WriteDeadletterStorage",
                        TextIO
                                .write()
                                .to(options.getDeadletterBucket())
                                .withWindowedWrites()
                                .withNumShards(10));

        return pipeline.run();
    }
}
