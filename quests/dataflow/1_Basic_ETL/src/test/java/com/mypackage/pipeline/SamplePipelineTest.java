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

import com.google.api.services.bigquery.model.TableRow;
import com.google.gson.Gson;
import org.apache.beam.sdk.testing.NeedsRunner;
import org.apache.beam.sdk.testing.PAssert;
import org.apache.beam.sdk.testing.TestPipeline;
import org.apache.beam.sdk.transforms.Create;
import org.apache.beam.sdk.transforms.ParDo;
import org.apache.beam.sdk.values.PCollection;
import org.junit.Rule;
import org.junit.Test;
import org.junit.experimental.categories.Category;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;

import java.time.Instant;

/**
 * Test cases for the {@link SamplePipeline} class.
 */
@RunWith(JUnit4.class)
public class SamplePipelineTest {

  @Rule
  public final transient TestPipeline pipeline = TestPipeline.create();

  /**
   * Tests whether {@link SamplePipeline.JsonToTableRowFn} correctly
   * converts Json to a TableRow
   */
  @Test
  @Category(NeedsRunner.class)
  public void testSamplePipeline() {

    Gson gson = new Gson();
    SamplePipeline.CommonLog cl = new SamplePipeline.CommonLog("1",
            "192.175.49.116", 37.751, -97.822, "2019-06-19T16:06:45.118306Z",
            "\"GET eucharya.html HTTP/1.0\"",
            "Mozilla/5.0 (compatible; MSIE 7.0; Windows NT 5.01; Trident/5.1)", 200, 500);

    String json = gson.toJson(cl);

    PCollection<TableRow> actual =
            pipeline
              .apply("Create", Create.of(json))
              .apply("Apply JsonToTableRowFn",
                      ParDo.of(new SamplePipeline.JsonToTableRowFn()));

    TableRow expected = new TableRow();
    expected.set("user_id", cl.user_id);
    expected.set("ip", cl.ip);
    expected.set("lat", cl.lat);
    expected.set("lng", cl.lng);
    expected.set("timestamp", Instant.parse(cl.timestamp).toString());
    expected.set("http_request", cl.http_request);
    expected.set("http_response", cl.http_response);
    expected.set("num_bytes", cl.num_bytes);
    expected.set("user_agent", cl.user_agent);



    PAssert.that(actual)
            .containsInAnyOrder(expected);

    pipeline.run();
  }
}
