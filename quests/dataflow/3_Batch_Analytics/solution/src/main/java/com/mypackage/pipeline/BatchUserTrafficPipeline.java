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
import org.apache.beam.sdk.io.TextIO;
import org.apache.beam.sdk.io.gcp.bigquery.BigQueryIO;
import org.apache.beam.sdk.options.Description;
import org.apache.beam.sdk.options.PipelineOptionsFactory;
import org.apache.beam.sdk.schemas.transforms.Group;
import org.apache.beam.sdk.schemas.transforms.Select;
import org.apache.beam.sdk.transforms.*;
import org.apache.beam.sdk.values.Row;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;


public class BatchUserTrafficPipeline {

    /**
     * The logger to output status messages to.
     */
    private static final Logger LOG = LoggerFactory.getLogger(BatchUserTrafficPipeline.class);

    /**
     * The {@link Options} class provides the custom execution options passed by the
     * executor at the command-line.
     */
    public interface Options extends DataflowPipelineOptions {
        @Description("Path to events.json")
        String getInputPath();
        void setInputPath(String inputPath);

        @Description("BigQuery table name")
        String getTableName();
        void setTableName(String tableName);
    }

    /**
     * The main entry-point for pipeline execution. This method will start the
     * pipeline but will not wait for it's execution to finish. If blocking
     * execution is required, use the {@link BatchUserTrafficPipeline#run(Options)} method to
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
        options.setJobName("my-pipeline-" + System.currentTimeMillis());

        /*
         * Steps:
         * 1) Read something
         * 2) Transform something
         * 3) Write something
         */

        pipeline
                // Read in lines from GCS and Parse to CommonLog
                .apply("ReadFromGCS", TextIO.read().from(options.getInputPath()))
                .apply("ParseJson", ParDo.of(new DoFn<String, CommonLog>() {
                                                 @ProcessElement
                                                 public void processElement(@Element String json, OutputReceiver<CommonLog> r) throws Exception {
                                                     Gson gson = new Gson();
                                                     CommonLog commonLog = gson.fromJson(json, CommonLog.class);
                                                     r.output(commonLog);
                                                 }
                                             }
                ))

                // Have to mention field twice, in case of multiple agg fields and multiple agg functions
                .apply("PerUserAggregations", Group.<CommonLog>byFieldNames("user_id")
                        .aggregateField("user_id", Count.combineFn(), "pageviews")
                        .aggregateField("num_bytes", Sum.ofLongs(), "total_bytes")
                        .aggregateField("num_bytes", Max.ofLongs(), "max_num_bytes")
                        .aggregateField("num_bytes", Min.ofLongs(), "min_num_bytes"))

                // Need a select statement to unnest the <"Key", "Value"> Row returned by the previous transform
                .apply("UnnestFields", Select.fieldNames("key.user_id", "value.pageviews", "value.total_bytes", "value.max_num_bytes", "value.min_num_bytes"))
                .apply("WriteToBQ",
                        BigQueryIO.<Row>write().to(options.getTableName()).useBeamSchema()
                                .withWriteDisposition(BigQueryIO.Write.WriteDisposition.WRITE_TRUNCATE)
                                .withCreateDisposition(BigQueryIO.Write.CreateDisposition.CREATE_IF_NEEDED));

        LOG.info("Building pipeline...");

        return pipeline.run();
    }
}