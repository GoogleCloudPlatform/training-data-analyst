
/*
 * Copyright (C) 2021 Google Inc.
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
import org.apache.beam.sdk.io.gcp.bigquery.BigQueryIO;
import org.apache.beam.sdk.io.gcp.pubsub.PubsubIO;
import org.apache.beam.sdk.options.Description;
import org.apache.beam.sdk.options.PipelineOptionsFactory;
import org.apache.beam.sdk.schemas.Schema;
import org.apache.beam.sdk.schemas.transforms.AddFields;
import org.apache.beam.sdk.schemas.transforms.Select;
import org.apache.beam.sdk.schemas.annotations.SchemaCreate;
import org.apache.beam.sdk.schemas.transforms.Filter;
import org.apache.beam.sdk.transforms.Count;
import org.apache.beam.sdk.transforms.PTransform;
import org.apache.beam.sdk.transforms.Combine;
import org.apache.beam.sdk.transforms.ParDo;
import org.apache.beam.sdk.transforms.DoFn;
import org.apache.beam.sdk.transforms.DoFn.*;
import org.apache.beam.sdk.transforms.windowing.FixedWindows;
import org.apache.beam.sdk.transforms.windowing.IntervalWindow;
import org.apache.beam.sdk.transforms.windowing.Window;
import org.apache.beam.sdk.transforms.windowing.AfterProcessingTime;
import org.apache.beam.sdk.transforms.windowing.AfterWatermark;
import org.apache.beam.sdk.values.PCollection;
import org.apache.beam.sdk.values.Row;
import org.joda.time.DateTime;
import org.joda.time.Duration;
import org.joda.time.Instant;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;


public class TaxiStreamingPipeline {

    /**
     * The logger to output status messages to.
     */
    private static final Logger LOG = LoggerFactory.getLogger(TaxiStreamingPipeline.class);

    /**
     * The {@link Options} class provides the custom execution options passed by the
     * executor at the command-line.
     */
    public interface Options extends DataflowPipelineOptions {

        @Description("BigQuery output table name")
        String getOutputTableName();
        void setOutputTableName(String outputTableName);

        @Description("Input topic name")
        String getInputTopic();
        void setInputTopic(String inputTopic);
    }

    /**
     * The main entry-point for pipeline execution. This method will start the
     * pipeline but will not wait for it's execution to finish. If blocking
     * execution is required, use the {@link StreamingMinuteTrafficPipeline#run(Options)} method to
     * start the pipeline and invoke {@code result.waitUntilFinish()} on the
     * {@link PipelineResult}.
     *
     * @param args The command-line args passed by the executor.
     */
    public static void main(String[] args) {
        Options options = PipelineOptionsFactory.fromArgs(args).withValidation().as(Options.class);

        run(options);
    }


    /**
     * A DoFn acccepting Json and outputing TaxiRide with Beam Schema
     */
    static class JsonToTaxiRide extends DoFn<String, TaxiRide> {

        @ProcessElement
        public void processElement(@Element String json, OutputReceiver<TaxiRide> r) throws Exception {
            Gson gson = new Gson();
            TaxiRide taxiRide = gson.fromJson(json, TaxiRide.class);
            r.output(taxiRide);
        }
    }

    /**
     * A Beam schema for counting pageviews per minute
     */
    public static final Schema taxiCountSchema = Schema
            .builder()
            .addInt64Field("no_rides")
            .addDateTimeField("minute")
            .build();

    public static class TaxiCountTransform extends PTransform<PCollection<String>, PCollection<Long>> {

        @Override
        public PCollection<Long> expand(PCollection<String> pcoll)
        {
            PCollection<Long> taxiCount =
                pcoll
                .apply("ParseJson", ParDo.of(new JsonToTaxiRide()))
                .apply("FilterForPickups", Filter.<TaxiRide>create().whereFieldName("ride_status", status -> "pickup".equals(status)))
                .apply("WindowByMinute", Window.<TaxiRide>into(FixedWindows.of(Duration.standardSeconds(60)))
                                                                .triggering(AfterWatermark.pastEndOfWindow()
                                                                    .withLateFirings(AfterProcessingTime.pastFirstElementInPane()))
                                                                .withAllowedLateness(Duration.standardMinutes(1))
                                                                .accumulatingFiredPanes())
                .apply("CountPerMinute", Combine.globally(Count.<TaxiRide>combineFn()).withoutDefaults());
        
                return taxiCount;
                }
            }


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
        options.setJobName("streaming-minute-taxi-pipeline-" + System.currentTimeMillis());

        /*
         * Steps:
         * 1) Read something
         * 2) Transform something
         * 3) Write something
         */

        pipeline
                .apply("ReadMessage", PubsubIO.readStrings()
                        .withTimestampAttribute("ts")
                        .fromTopic(options.getInputTopic()))
                .apply("TaxiCount", new TaxiCountTransform())
                .apply("ConvertToRow", ParDo.of(new DoFn<Long, Row>() {
                    @ProcessElement
                    public void processElement(@Element Long rides, OutputReceiver<Row> r, IntervalWindow window) {
                        Instant i = Instant.ofEpochMilli(window.start().getMillis());
                        Row row = Row.withSchema(taxiCountSchema)
                                .addValues(rides, i)
                                .build();
                        r.output(row);
                    }
                })).setRowSchema(taxiCountSchema)
                // Streaming insert of aggregate data
                .apply("WriteAggregateToBQ",
                        BigQueryIO.<Row>write().to(options.getOutputTableName()).useBeamSchema()
                                .withWriteDisposition(BigQueryIO.Write.WriteDisposition.WRITE_APPEND)
                                .withCreateDisposition(BigQueryIO.Write.CreateDisposition.CREATE_IF_NEEDED));

        LOG.info("Building pipeline...");

        return pipeline.run();
    }
}
