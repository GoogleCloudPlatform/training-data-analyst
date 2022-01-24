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
package scio.mypackage.pipeline

//TODO: Add imports

/**
 * The {@link BatchMinuteTrafficOptions} class provides the custom execution options passed by the
 * executor at the command-line.
 */
trait BatchMinuteTrafficOptions extends PipelineOptions {
}

//TODO: Add CommonLog Class

/**
 * A DoFn acccepting Json and outputing CommonLog with Beam Schema
 */
case class JsonToCommonLog() extends DoFn[String, CommonLog] {
  var gson: Gson = _

  @Setup
  def setup(): Unit = {
    gson = new Gson
  }
  @ProcessElement
  def processElement(c: ProcessContext): Unit = {
    val commonLog: CommonLog = gson.fromJson(c.element(), classOf[CommonLog])
    c.output(commonLog)
  }
}

object BatchMinuteTraffic {
  /**
   * The logger to output status messages to.
   */
  private val LOG = LoggerFactory.getLogger(this.getClass)

  /**
   * A Beam schema for counting pageviews per minute
   */
  val  pageViewsSchema: Schema = Schema
    .builder()
    .addInt64Field("page_views")
    .addDateTimeField("minute")
    .build();

  /**
   * The main entry-point for pipeline execution. This method will start the
   * pipeline but will not wait for it's execution to finish. If blocking
   * execution is required, use the {@link BatchMinuteTraffic# run ( BatchMinuteTrafficOptions )} method to
   * start the pipeline.
   *
   * @param args The command-line args passed by the executor.
   */
  def main(cmdlineArgs: Array[String]): Unit = {

    // Setting up the Beam pipeline options
    val pipelineOptions = PipelineOptionsFactory
      .fromArgs(cmdlineArgs: _*)
      .withValidation
      .as(classOf[BatchMinuteTrafficOptions])

    implicit val rowCoder: Coder[Row] = Coder.beam[Row](RowCoder.of(pageViewsSchema))

    // Create the pipeline
    val sc = ScioContext(pipelineOptions)

    //Step1: Read events
    val read_event =  sc
      .withName("Read events")
      .textFile(pipelineOptions.getInputFiles())

    //Step2: Transform to common log
    val transformed_event = read_event.withName("ParseJson")
      .applyTransform(ParDo.of(JsonToCommonLog()))

    //Step3: TODO: Calculate record count for each window with fixed duration of 1 Minute

    /* Step4: TODO: Transform windowed record count into PageView Beam Row
    with schema containing page_views and window start time as fields */
    // val pageViewsByWindow: SCollection[Row]

    // Step5: Write output to BigQuery
    pageViewsByWindow
      .saveAsCustomOutput(
        "Write output To BigQuery",
        BigQueryIO
          .write[Row]()
          .to(pipelineOptions.getOutputTableSpec())
          .withCustomGcsTempLocation(StaticValueProvider.of(pipelineOptions.getTempLocation))
          .useBeamSchema()
          .withWriteDisposition(BigQueryIO.Write.WriteDisposition.WRITE_TRUNCATE)
          .withCreateDisposition(BigQueryIO.Write.CreateDisposition.CREATE_IF_NEEDED))

    // Runs the pipeline to completion with the specified options.
    sc.run()
  }
}