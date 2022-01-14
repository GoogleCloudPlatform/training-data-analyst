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
import com.spotify.scio.bigquery._
import com.google.gson.Gson
import com.spotify.scio.ScioContext
import com.spotify.scio.values.SCollection
import org.apache.beam.sdk.io.gcp.bigquery.BigQueryIO
import org.apache.beam.sdk.options.{Default, Description, PipelineOptions, PipelineOptionsFactory}
import org.apache.beam.sdk.options.ValueProvider.StaticValueProvider
import org.apache.beam.sdk.transforms.{Count, ParDo}
import org.apache.beam.sdk.transforms.{DoFn}
import org.apache.beam.sdk.transforms.DoFn.{ProcessElement, Setup}
import org.slf4j.LoggerFactory

import scala.jdk.CollectionConverters._
import scala.util.Random

trait BatchUserTrafficOptions extends PipelineOptions {

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

class UserTraffic(var page_views: Int, var total_bytes: Long, var max_num_bytes: Long, var min_num_bytes: Long)

object BatchUserTraffic {
  private val LOG = LoggerFactory.getLogger(BatchUserTraffic.getClass)

  val random = new Random()

  def sequenceFn(accumulator: UserTraffic, numBytes: Long): UserTraffic = {
    accumulator.page_views += 1
    accumulator.total_bytes += numBytes
    accumulator.max_num_bytes = Math.max(accumulator.max_num_bytes, numBytes)
    accumulator.min_num_bytes = Math.min(accumulator.min_num_bytes, numBytes)
    accumulator
  }

  def combineFn(accumulator1: UserTraffic, accumulator2: UserTraffic): UserTraffic = {
    accumulator1.page_views += accumulator2.page_views
    accumulator1.total_bytes += accumulator2.total_bytes
    accumulator1.max_num_bytes = Math.max(accumulator1.max_num_bytes, accumulator2.max_num_bytes)
    accumulator1.min_num_bytes = Math.min(accumulator1.min_num_bytes, accumulator2.min_num_bytes)
    accumulator1
  }

  def main(cmdlineArgs: Array[String]): Unit = {
    val pipelineOptions = PipelineOptionsFactory
      .fromArgs(cmdlineArgs: _*)
      .withValidation
      .as(classOf[BatchUserTrafficOptions])

    val sc = ScioContext(pipelineOptions)

    val useridBytesPair: SCollection[(String, Long)] = sc
      .withName("Read events")
      .textFile(pipelineOptions.getInputFiles())
      .withName("ParseJson")
      .applyTransform(ParDo.of(JsonToCommonLog()))
      .withName("Get num_bytes by user id")
      .map(e => (e.user_id, e.num_bytes))

    val userTrafficByUser: SCollection[(String, UserTraffic)] =useridBytesPair
      .withName("PerUserAggregations")
      .aggregateByKey(new UserTraffic(0, 0L, 0L, 0L))(
        sequenceFn,combineFn)

    writeUsingCustomOutput(userTrafficByUser, pipelineOptions)

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
