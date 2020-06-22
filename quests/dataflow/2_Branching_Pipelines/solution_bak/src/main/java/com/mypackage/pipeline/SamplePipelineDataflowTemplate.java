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

import com.google.common.annotations.VisibleForTesting;
import com.google.gson.Gson;
import org.apache.beam.runners.dataflow.options.DataflowPipelineOptions;
import org.apache.beam.sdk.Pipeline;
import org.apache.beam.sdk.PipelineResult;
import org.apache.beam.sdk.io.TextIO;
import org.apache.beam.sdk.io.gcp.bigquery.BigQueryIO;
import org.apache.beam.sdk.options.Description;
import org.apache.beam.sdk.options.PipelineOptionsFactory;
import org.apache.beam.sdk.options.ValueProvider;
import org.apache.beam.sdk.schemas.JavaFieldSchema;
import org.apache.beam.sdk.schemas.Schema;
import org.apache.beam.sdk.schemas.annotations.DefaultSchema;
import org.apache.beam.sdk.schemas.transforms.AddFields;
import org.apache.beam.sdk.schemas.transforms.Convert;
import org.apache.beam.sdk.schemas.transforms.DropFields;
import org.apache.beam.sdk.schemas.transforms.Filter;
import org.apache.beam.sdk.transforms.DoFn;
import org.apache.beam.sdk.transforms.MapElements;
import org.apache.beam.sdk.transforms.ParDo;
import org.apache.beam.sdk.transforms.SimpleFunction;
import org.apache.beam.sdk.values.PCollection;
import org.apache.beam.sdk.values.Row;
import org.joda.time.DateTime;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class SamplePipelineDataflowTemplate {

  /*
   * The logger to output status messages to.
   */
  private static final Logger LOG = LoggerFactory.getLogger(MyPipeline.class);

  /**
   * The {@link Options} class provides the custom execution options passed by the
   * executor at the command-line.
   */
  public interface Options extends DataflowPipelineOptions {
    @Description("Path to events.json")
    ValueProvider<String> getInputPath();
    void setInputPath(ValueProvider<String> inputPath);

    @Description("Path to coldline storage bucket")
    ValueProvider<String> getOutputPath();
    void setOutputPath(ValueProvider<String> outputPath);

    @Description("BigQuery table name")
    ValueProvider<String> getTableName();
    void setTableName(ValueProvider<String> tableName);
  }

  @VisibleForTesting
  /**
   * A class used for parsing JSON web server events
   */
  @DefaultSchema(JavaFieldSchema.class)
  public static class CommonLog {
    String user_id;
    String ip;
    float lat;
    float lng;
    String timestamp;
    String http_request;
    @javax.annotation.Nullable String user_agent;
    int http_response;
    int num_bytes;
  }

  @VisibleForTesting
  /**
   * A class used for parsing JSON web server events
   */
  @DefaultSchema(JavaFieldSchema.class)
  public static class CommonLogDateTime {
    String user_id;
    String ip;
    float lat;
    float lng;
    String timestamp;
    String http_request;
    @javax.annotation.Nullable String user_agent;
    int http_response;
    int num_bytes;
  }


  @VisibleForTesting
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
   * The main entry-point for pipeline execution. This method will start the
   * pipeline but will not wait for it's execution to finish. If blocking
   * execution is required, use the {@link SamplePipelineDataflowTemplate#run(Options)} method to
   * start the pipeline and invoke {@code result.waitUntilFinish()} on the
   * {@link PipelineResult}.
   *
   * @param args The command-line args passed by the executor.
   */
  public static void main(String[] args) {
    PipelineOptionsFactory.register(Options.class);
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
    options.setJobName("sample-pipeline-" + System.currentTimeMillis());

    /*
     * Steps:
     * 1) Read something
     * 2) Transform something
     * 3) Write something
     */

    PCollection<String> lines = pipeline.apply("ReadFromGCS", TextIO.read().from(options.getInputPath()));

    // Write to Google Cloud Storage
    lines.apply("WriteRawToGCS", TextIO.write().to(options.getOutputPath()));

    // Convert elemnts, filter individual elements, and write to BigQuery
    lines.apply("ParseJson", ParDo.of(new JsonToCommonLog()))
            // TODO: make sure to import the right filter
            .apply(Convert.toRows())
            .apply("FilterFn", Filter.<Row>create().whereFieldName("num_bytes", (Integer num_bytes) -> num_bytes > 120))
            .apply("SelectElements", DropFields.fields("lat", "lng"))
//            .apply(Convert.toRows())
            // by default fields are NULLABLE so add `false` to make required
            // TODO: mention default and NULLABLE
            .apply("Add DateTime Column", AddFields.<Row>create().field("timestamp_joda", Schema.FieldType.DATETIME))
            .apply("Create new row", MapElements.via(new SimpleFunction<Row, Row>() {
              @Override
              public Row apply(Row row) {
                DateTime dateTime = new DateTime(row.getString("timestamp"));
                return Row.withSchema(row.getSchema())
                        .addValues(
                                row.getString("user_id"),
                                row.getString("ip"),
                                row.getString("timestamp"),
                                row.getString("http_request"),
                                row.getString("user_agent"),
                                row.getInt32("http_response"),
                                row.getInt32("num_bytes"),
                                dateTime)
                        .build();
              }
            }))
            .apply("WriteToBQ",
                    BigQueryIO.<Row>write().to(options.getTableName()).useBeamSchema()
                            .withWriteDisposition(BigQueryIO.Write.WriteDisposition.WRITE_TRUNCATE)
                            .withCreateDisposition(BigQueryIO.Write.CreateDisposition.CREATE_IF_NEEDED));
    LOG.info("Building pipeline...");

    return pipeline.run();
  }
}