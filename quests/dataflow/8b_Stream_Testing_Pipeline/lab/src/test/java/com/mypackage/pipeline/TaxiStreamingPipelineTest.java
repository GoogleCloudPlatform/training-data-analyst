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

import com.mypackage.pipeline.TaxiStreamingPipeline.*;
import java.util.Arrays;
import java.util.List;
import java.util.Collections;
import org.apache.beam.sdk.coders.StringUtf8Coder;
import org.apache.beam.sdk.schemas.SchemaCoder;
import org.apache.beam.sdk.testing.PAssert;
import org.apache.beam.sdk.testing.TestPipeline;
import org.apache.beam.sdk.testing.ValidatesRunner;
import org.apache.beam.sdk.testing.TestStream;
import org.apache.beam.sdk.transforms.Create;
import org.apache.beam.sdk.transforms.DoFn;
import org.apache.beam.sdk.transforms.MapElements;
import org.apache.beam.sdk.transforms.ParDo;
import org.apache.beam.sdk.values.PCollection;
import org.apache.beam.sdk.testing.NeedsRunner;
import org.apache.beam.sdk.schemas.AutoValueSchema;
import org.apache.beam.sdk.schemas.Schema;
import org.apache.beam.sdk.values.Row;
import org.apache.beam.sdk.values.TimestampedValue;
import org.apache.beam.sdk.transforms.windowing.IntervalWindow;
import org.joda.time.Duration;
import org.joda.time.Instant;
import org.junit.Rule;
import org.junit.Test;
import org.junit.experimental.categories.Category;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;

/** Tests of TaxiStreamingPipeline. */
@RunWith(JUnit4.class)
public class TaxiStreamingPipelineTest {

  @Rule 
  public final transient TestPipeline p = TestPipeline.create();

  /** Test simple windowing behavior (no late data) and filter*/
  @Test
  @Category(NeedsRunner.class)
  public void testTaxiRideWindowing() throws Exception {

    Instant startTime = new Instant(0);
    
    String json = "{\"ride_id\":\"x\",\"point_idx\":1,\"latitude\":0.0,"
                  + "\"longitude\":0.0,\"timestamp\":\"00:00:00\",\"meter_reading\":1.0,"
                  +  "\"meter_increment\":0.1,\"ride_status\":\"%s\",\"passenger_count\":1}";

    TestStream<String> createEvents = TestStream.create(StringUtf8Coder.of())
    .advanceWatermarkTo(startTime)
    .addElements(
      TimestampedValue.of(json.format(json, "pickup"),
                          startTime),
      TimestampedValue.of(json.format(json, "enroute"),
                          startTime),
      TimestampedValue.of(json.format(json, "pickup"),
                          startTime))
    .addElements(
      TimestampedValue.of(json.format(json, "pickup"),
                          startTime.plus(Duration.standardMinutes(1))))
    .advanceWatermarkTo(startTime.plus(Duration.standardMinutes(1)))
    .addElements(    
      TimestampedValue.of(json.format(json, "pickup"),
                          startTime.plus(Duration.standardMinutes(2))))               
    .advanceWatermarkToInfinity();

    PCollection<Long> outputCount = p
                                    .apply(createEvents)
                                    .apply(new TaxiCountTransform());

    IntervalWindow window1 = new IntervalWindow(startTime, 
                                                startTime.plus(Duration.standardMinutes(1)));
    IntervalWindow window2 = new IntervalWindow(startTime.plus(Duration.standardMinutes(1)), 
                                                startTime.plus(Duration.standardMinutes(2)));
    IntervalWindow window3 = new IntervalWindow(startTime.plus(Duration.standardMinutes(2)), 
                                                startTime.plus(Duration.standardMinutes(3)));

    PAssert.that(outputCount).inWindow(window1).containsInAnyOrder(2L);
    PAssert.that(outputCount).inWindow(window2).containsInAnyOrder(1L);
    PAssert.that(outputCount).inWindow(window3).containsInAnyOrder(1L);

    p.run().waitUntilFinish();
  }

  /* UNCOMMENT FOR TASK 3 */

  // @Test
  // @Category(NeedsRunner.class)
  // public void testTaxiRideLateData() throws Exception {

  //   Instant startTime = new Instant(0);
    
  //   String json = "{\"ride_id\":\"x\",\"point_idx\":1,\"latitude\":0.0,"
  //                 + "\"longitude\":0.0,\"timestamp\":\"00:00:00\",\"meter_reading\":1.0,"
  //                 +  "\"meter_increment\":0.1,\"ride_status\":\"%s\",\"passenger_count\":1}";

  //   TestStream<String> createEvents = /* CreateTestStream */

  //   PCollection<Long> outputCount = p
  //                                   .apply(createEvents)
  //                                   .apply(new TaxiCountTransform());

  //   IntervalWindow window1 = new IntervalWindow(startTime, 
  //                                               startTime.plus(Duration.standardMinutes(1)));

  //   PAssert.that(outputCount).inOnTimePane(window1).containsInAnyOrder(2L);
  //   PAssert.that(outputCount).inFinalPane(window1).containsInAnyOrder(3L);

  //   p.run().waitUntilFinish();
  // }
}
