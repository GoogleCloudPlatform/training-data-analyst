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
import com.google.gson.JsonSyntaxException;
import org.apache.beam.sdk.Pipeline;
import org.apache.beam.sdk.PipelineResult;
import org.apache.beam.sdk.io.TextIO;
import org.apache.beam.sdk.io.gcp.bigquery.BigQueryIO;
import org.apache.beam.sdk.io.gcp.pubsub.PubsubIO;
import org.apache.beam.sdk.options.Description;
import org.apache.beam.sdk.options.PipelineOptions;
import org.apache.beam.sdk.options.PipelineOptionsFactory;
import org.apache.beam.sdk.schemas.Schema;
import org.apache.beam.sdk.transforms.*;
import org.apache.beam.sdk.transforms.windowing.*;
import org.apache.beam.sdk.values.*;
import org.joda.time.Duration;
import org.joda.time.Instant;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * The {@link StreamingMinuteTrafficPipeline} is a sample pipeline which can be used as a base for creating a real
 * Dataflow pipeline.
 *
 * <p><b>Pipeline Requirements</b>
 *
 * <ul>
 *   <li>Requirement #1
 *   <li>Requirement #2
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
 * -Dexec.mainClass=com.mypackage.pipeline.BatchUserTrafficPipeline \
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
    public interface Options extends PipelineOptions {
        @Description("Window duration length, in seconds")
        Integer getWindowDuration();
        void setWindowDuration(Integer windowDuration);

        @Description("BigQuery table name")
        String getOutputTableName();
        void setOutputTableName(String outputTableName);

        @Description("Input topic name")
        String getInputTopic();
        void setInputTopic(String inputTopic);


        @Description("Window allowed lateness, in days")
        Integer getAllowedLateness();
        void setAllowedLateness(Integer allowedLateness);

        @Description("The Cloud Storage bucket used for writing " + "unparseable Pubsub Messages.")
        String getDeadletterBucket();
        void setDeadletterBucket(String deadletterBucket);

    }

    /**
     * A PTransform accepting Json and outputting tagged CommonLog with Beam Schema or raw Json string if parsing fails
     */
    public static class PubsubMessageToCommonLog extends PTransform<PCollection<String>, PCollectionTuple> {
        @Override
        public PCollectionTuple expand(PCollection<String> input) {
            return input
                    .apply("JsonToCommonLog", ParDo.of(new DoFn<String, CommonLog>() {
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


    public static final Schema pageviewsSchema = Schema.builder()
            .addInt64Field("pageviews")
            //TODO: change window_end in other labs
            .addDateTimeField("window_end")
            .build();
    public static final Schema rawSchema = Schema.builder()
            .addStringField("user_id")
            .addDateTimeField("event_timestamp")
            .addDateTimeField("processing_timestamp")
            .build();

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
        Options options = PipelineOptionsFactory.fromArgs(args)
                .withValidation()
                .as(Options.class);
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

        /*
         * Steps:
         *  1) Read something
         *  2) Transform something
         *  3) Write something
         */

        LOG.info("Building pipeline...");


        PCollectionTuple transformOut =
                pipeline.apply("ReadPubSubMessages", PubsubIO.readStrings()
                        // Retrieve timestamp information from Pubsub Message attributes
                        .withTimestampAttribute("timestamp")
                        .fromTopic(options.getInputTopic()))
                        .apply("ConvertMessageToCommonLog", new PubsubMessageToCommonLog());

        // Write parsed messages to BigQuery
        transformOut
                // Retrieve parsed messages
                .get(parsedMessages)
                .apply("WindowByMinute", Window.<CommonLog>into(
                        FixedWindows.of(Duration.standardSeconds(options.getWindowDuration()))).withAllowedLateness(
                        Duration.standardDays(options.getAllowedLateness()))
                        .triggering(AfterWatermark.pastEndOfWindow()
                                .withLateFirings(AfterPane.elementCountAtLeast(1)))
                        .accumulatingFiredPanes())
                // update to Group.globally() after resolved: https://issues.apache.org/jira/browse/BEAM-10297
                // Only if supports Row output
                .apply("CountPerMinute", Combine.globally(Count.<CommonLog>combineFn())
                        .withoutDefaults())
                .apply("ConvertToRow", ParDo.of(new DoFn<Long, Row>() {
                    @ProcessElement
                    public void processElement(@Element Long views, OutputReceiver<Row> r, IntervalWindow window) {
                        Instant i = Instant.ofEpochMilli(window.end()
                                .getMillis());
                        Row row = Row.withSchema(pageviewsSchema)
                                .addValues(views, i)
                                .build();
                        r.output(row);
                    }
                }))
                .setRowSchema(pageviewsSchema)
                // TODO: is this a streaming insert?
                .apply("WriteToBQ", BigQueryIO.<Row>write().to(options.getOutputTableName())
                        .useBeamSchema()
                        .withWriteDisposition(BigQueryIO.Write.WriteDisposition.WRITE_APPEND)
                        .withCreateDisposition(BigQueryIO.Write.CreateDisposition.CREATE_IF_NEEDED));

        // Write unparsed messages to Cloud Storage
        transformOut
                // Retrieve unparsed messages
                .get(unparsedMessages)
                .apply("FireEvery10s", Window.<String>configure().triggering(
                        Repeatedly.forever(
                        AfterProcessingTime.pastFirstElementInPane()
                                .plusDelayOf(Duration.standardSeconds(10))))
                        .discardingFiredPanes())
                .apply("WriteDeadletterStorage", TextIO.write()
                        //TODO: change this to actual full parameter
                        .to(options.getDeadletterBucket() + "/deadletter/*")
                        .withWindowedWrites()
                        .withNumShards(10));


        return pipeline.run();
    }
}

