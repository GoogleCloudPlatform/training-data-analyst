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

import com.google.api.services.bigquery.model.{TableFieldSchema, TableSchema}
import com.google.gson.Gson
import com.spotify.scio.ScioContext
import com.spotify.scio.bigquery.{TableRow}
import com.spotify.scio.values.SCollection
import org.apache.beam.sdk.io.gcp.bigquery.BigQueryIO
import org.apache.beam.sdk.options.ValueProvider.StaticValueProvider
import org.apache.beam.sdk.options.{Default, Description, PipelineOptions, PipelineOptionsFactory}
import org.apache.beam.sdk.transforms.{DoFn, ParDo}
import org.apache.beam.sdk.transforms.DoFn.{ProcessElement, Setup}
import org.slf4j.LoggerFactory
import scala.jdk.CollectionConverters._

trait MyPipelineOptions extends PipelineOptions {

  @Description("Input file or file pattern. E.g: gs://bucket/prefix/*.json")
  def getInputFiles(): String
  def setInputFiles(value: String): Unit


  @Description("Output BigQuery table name in the form of <ProjectId>:<DatasetId>.<Tablename>")
  def getOutputTableSpec(): String
  def setOutputTableSpec(value: String): Unit

}

case class CommonLog(user_id: String, ip: String, lat: Double, lng: Double, timestamp: String, http_request: String, user_agent: String, http_response: Long, num_bytes:Long)

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

object MyPipeline {
  private val LOG = LoggerFactory.getLogger(this.getClass)

  def main(cmdlineArgs: Array[String]): Unit = {
    val pipelineOptions = PipelineOptionsFactory
      .fromArgs(cmdlineArgs: _*)
      .withValidation
      .as(classOf[MyPipelineOptions])

    val sc = ScioContext(pipelineOptions)

    // Step1: Read event
    val read_event = sc.withName("Read events")
      .textFile(pipelineOptions.getInputFiles())

    // Step2: Transform to CommonLog
    val commonLogRecords: SCollection[CommonLog] = read_event.withName("Convert to CommonLog")
      .applyTransform(ParDo.of(JsonToCommonLog()))

    // Step3: Write output to BigQuery
    writeUsingCustomOutput(commonLogRecords, pipelineOptions)

    sc.run()
  }

  def writeUsingCustomOutput(commonLogRecords: SCollection[CommonLog], pipelineOptions: MyPipelineOptions): Unit = {
    val tableSchema = new TableSchema().setFields(
      List(
        new TableFieldSchema().setName("user_id").setType("STRING"),
        new TableFieldSchema().setName("ip").setType("STRING"),
        new TableFieldSchema().setName("lat").setType("FLOAT"),
        new TableFieldSchema().setName("lng").setType("FLOAT"),
        new TableFieldSchema().setName("timestamp").setType("STRING"),
        new TableFieldSchema().setName("http_request").setType("STRING"),
        new TableFieldSchema().setName("user_agent").setType("STRING"),
        new TableFieldSchema().setName("http_response").setType("INTEGER"),
        new TableFieldSchema().setName("num_bytes").setType("INTEGER"),
      ).asJava
    )

    commonLogRecords.saveAsCustomOutput(
      "Write CommonLog To BigQuery",
      BigQueryIO
        .write[CommonLog]()
        .to(pipelineOptions.getOutputTableSpec())
        .withFormatFunction((e: CommonLog) => {
          new TableRow()
            .set("user_id",e.user_id)
            .set("ip", e.ip)
            .set("lat", e.lat)
            .set("lng",e.lng)
            .set("timestamp", e.timestamp)
            .set("http_request", e.http_request)
            .set("user_agent",e.user_agent)
            .set("http_response",e.http_response)
            .set("num_bytes",e.num_bytes)
        })
        .withCustomGcsTempLocation(StaticValueProvider.of(pipelineOptions.getTempLocation))
        .withSchema(tableSchema)
        .withWriteDisposition(BigQueryIO.Write.WriteDisposition.WRITE_TRUNCATE)
        .withCreateDisposition(BigQueryIO.Write.CreateDisposition.CREATE_IF_NEEDED))
  }
}