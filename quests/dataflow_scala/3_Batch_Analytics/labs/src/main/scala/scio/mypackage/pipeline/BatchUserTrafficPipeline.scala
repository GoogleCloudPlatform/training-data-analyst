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
 * The {@link BatchUserTrafficOptions} class provides the custom execution options passed by the
 * executor at the command-line.
 */
trait BatchUserTrafficOptions extends PipelineOptions {
}

//TODO: Add CommonLog Class

// TODO: Add A DoFn acccepting Json and outputing CommonLog with Beam Schema

//TODO: Add UserTraffic Class

object BatchUserTraffic {
  /**
   * The logger to output status messages to.
   */
  private val LOG = LoggerFactory.getLogger(BatchUserTraffic.getClass)

  /**
   * The main entry-point for pipeline execution. This method will start the
   * pipeline but will not wait for it's execution to finish. If blocking
   * execution is required, use the {@link BatchUserTraffic# run ( BatchUserTrafficOptions )} method to
   * start the pipeline.
   *
   * @param args The command-line args passed by the executor.
   */
  def main(cmdlineArgs: Array[String]): Unit = {

    // Setting up the Beam pipeline options
    val pipelineOptions = PipelineOptionsFactory
      .fromArgs(cmdlineArgs: _*)
      .withValidation
      .as(classOf[BatchUserTrafficOptions])

    // Create the pipeline
    val sc = ScioContext(pipelineOptions)

    //Step1: Read events
    val read_event =  sc
      .withName("Read events")
      .textFile(pipelineOptions.getInputFiles())

    //Step2: Transform to common log
    val transformed_event = read_event.withName("ParseJson")
      .applyTransform(ParDo.of(JsonToCommonLog()))

    //Step3: Aggregate num_bytes by user_id
    val useridBytesPair = transformed_event.withName("Get num_bytes by user id")
      .map(e => (e.user_id, e.num_bytes))

    // Step4: TODO: Aggregate traffic by user using combine functionality
    // val userTrafficByUser: SCollection[(String, UserTraffic)]

    // Step5: Write output to BigQuery
    writeUsingCustomOutput(userTrafficByUser, pipelineOptions)

    // Runs the pipeline to completion with the specified options.
    sc.run()
  }

  def writeUsingCustomOutput(userTrafficByUser: SCollection[(String, UserTraffic)], pipelineOptions: BatchUserTrafficOptions): Unit = {
    val tableSchema = new TableSchema().setFields(
      List(
        new TableFieldSchema().setName("user_id").setType("STRING"),
        new TableFieldSchema().setName("page_views").setType("INTEGER"),
        new TableFieldSchema().setName("total_bytes").setType("INT64"),
        new TableFieldSchema().setName("max_num_bytes").setType("INT64"),
        new TableFieldSchema().setName("min_num_bytes").setType("INT64"),
      ).asJava
    )

    // Convert to TableRows
    val userTrafficRows: SCollection[TableRow] = userTrafficByUser
      .withName("Convert to tablerows")
      .map {
        case (userid: String, userTraffic: UserTraffic) =>
          new TableRow()
            .set("user_id", userid)
            .set("page_views", userTraffic.page_views)
            .set("total_bytes", userTraffic.total_bytes)
            .set("max_num_bytes", userTraffic.max_num_bytes)
            .set("min_num_bytes", userTraffic.min_num_bytes)
      }

    userTrafficRows
      .saveAsCustomOutput(
        "Write UserTraffic To BigQuery",
        BigQueryIO
          .writeTableRows()
          .to(pipelineOptions.getOutputTableSpec())
          .withCustomGcsTempLocation(StaticValueProvider.of(pipelineOptions.getTempLocation))
          .withSchema(tableSchema)
          .withWriteDisposition(BigQueryIO.Write.WriteDisposition.WRITE_TRUNCATE)
          .withCreateDisposition(BigQueryIO.Write.CreateDisposition.CREATE_IF_NEEDED))
  }
}
