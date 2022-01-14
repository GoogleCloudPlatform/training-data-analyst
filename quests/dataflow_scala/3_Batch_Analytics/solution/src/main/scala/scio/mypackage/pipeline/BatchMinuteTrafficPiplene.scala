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

import com.spotify.scio.ScioContext
import com.spotify.scio.coders.Coder
import com.spotify.scio.values.SCollection
import org.apache.beam.sdk.coders.RowCoder
import org.apache.beam.sdk.io.gcp.bigquery.BigQueryIO
import org.apache.beam.sdk.options.{Default, Description, PipelineOptions, PipelineOptionsFactory}
import org.apache.beam.sdk.options.ValueProvider.StaticValueProvider
import org.apache.beam.sdk.schemas.Schema
import org.apache.beam.sdk.transforms.ParDo
import org.apache.beam.sdk.transforms.windowing.IntervalWindow
import org.joda.time.{Duration, Instant}
import org.slf4j.LoggerFactory
import org.apache.beam.sdk.values.Row

trait BatchMinuteTrafficOptions extends PipelineOptions {

  @Description("Input file or file pattern. E.g: gs://bucket/prefix/*.json")
  def getInputFiles(): String
  def setInputFiles(value: String): Unit

  @Description("Output BigQuery table name in the form of <ProjectId>:<DatasetId>.<Tablename>")
  def getOutputTableSpec(): String
  def setOutputTableSpec(value: String): Unit
}

object BatchMinuteTraffic {
  private val LOG = LoggerFactory.getLogger(this.getClass)

  val  pageViewsSchema: Schema = Schema
    .builder()
    .addInt64Field("page_views")
    .addDateTimeField("minute")
    .build();


  def main(cmdlineArgs: Array[String]): Unit = {

    val pipelineOptions = PipelineOptionsFactory
      .fromArgs(cmdlineArgs: _*)
      .withValidation
      .as(classOf[BatchMinuteTrafficOptions])

    implicit val rowCoder: Coder[Row] = Coder.beam[Row](RowCoder.of(pageViewsSchema))
    val sc = ScioContext(pipelineOptions)

    val windowedRecordCount =
      sc
        .withName("Read events")
        .textFile(pipelineOptions.getInputFiles())
        .withName("ParseJson")
        .applyTransform(ParDo.of(JsonToCommonLog()))
        .withName("Add Timestamp")
        .timestampBy(e => new Instant(e.timestamp))
        .withName("WindowByMinute")
        .withFixedWindows(Duration.standardMinutes(1))
        .withName("Count records")
        .count

    val pageViewsByWindow: SCollection[Row] =
      windowedRecordCount
        .withWindow[IntervalWindow]
        .withName("Format PageViews")
        .map { case (page_views: Long, window: IntervalWindow) =>
          Row
            .withSchema(pageViewsSchema)
            .withFieldValue("page_views",page_views)
            .withFieldValue("minute",window.start())
            .build()
        }

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

    sc.run()
  }
}