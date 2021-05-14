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

import com.mypackage.pipeline.WeatherStatisticsPipeline.*;
import java.util.Arrays;
import java.util.List;
import java.util.Collections;
import org.apache.beam.sdk.coders.StringUtf8Coder;
import org.apache.beam.sdk.testing.PAssert;
import org.apache.beam.sdk.testing.TestPipeline;
import org.apache.beam.sdk.testing.ValidatesRunner;
import org.apache.beam.sdk.transforms.Create;
import org.apache.beam.sdk.transforms.DoFn;
import org.apache.beam.sdk.transforms.MapElements;
import org.apache.beam.sdk.transforms.ParDo;
import org.apache.beam.sdk.values.PCollection;
import org.apache.beam.sdk.testing.NeedsRunner;
import org.apache.beam.sdk.schemas.AutoValueSchema;
import org.apache.beam.sdk.schemas.Schema;
import org.apache.beam.sdk.values.Row;
import org.junit.Rule;
import org.junit.Test;
import org.junit.experimental.categories.Category;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;

/** Tests of WeatherStatistics. */
@RunWith(JUnit4.class)
public class WeatherStatisticsPipelineTest {

  @Rule 
  public final transient TestPipeline p = TestPipeline.create();

  /** Example unit test that tests a specific {@link DoFn}. */
  @Test
  @Category(NeedsRunner.class)
  public void testConvertCsvToWeatherRecord() throws Exception {
    String testInput = "x,31.4,-39.2,2/2/21,4.0,7.5,0.1";
    List<String> input = Arrays.asList(testInput);
    PCollection<WeatherRecord> output =
        p.apply(Create.of(input))
         .apply(ParDo.of(new ConvertCsvToWeatherRecord()));
    
    WeatherRecord testOutput = new WeatherRecord("x", 31.4, -39.2, "2/2/21", 4.0, 7.5, 0.1);

    PAssert.that(output).containsInAnyOrder(testOutput);
    p.run().waitUntilFinish();
  }

  @Test
  @Category(NeedsRunner.class)
  public void testConvertTempUnits() throws Exception {
    WeatherRecord testInput = new WeatherRecord("x", 31.4, -39.2, "2/2/21", 4.0, 7.5, 0.1);
    List<WeatherRecord> input = Arrays.asList(testInput);
    PCollection<WeatherRecord> output =
        p.apply(Create.of(input))
         .apply(ParDo.of(new ConvertTempUnits()));
    
    WeatherRecord testOutput = new WeatherRecord("x", 31.4, -39.2, "2/2/21", 39.2, 45.5, 0.1);

    PAssert.that(output).containsInAnyOrder(testOutput);
    p.run().waitUntilFinish();
  }

  @Test
  @Category(NeedsRunner.class)
  public void testComputeStatistics() throws Exception {

    WeatherRecord[] testInputs = new WeatherRecord[3];
    testInputs[0] = new WeatherRecord("x", 31.4, -39.2, "2/2/21", 39.2, 45.5, 0.1);
    testInputs[1] = new WeatherRecord("x", 31.4, -39.2, "2/2/21", 34.2, 39.5, 0.3);
    testInputs[2] = new WeatherRecord("y", 33.4, -49.2, "2/2/21", 72.5, 82.5, 0.5);

    List<WeatherRecord> input = Arrays.asList(testInputs);
    PCollection<String> output =
        p.apply(Create.of(input))
         .apply(new ComputeStatistics());
    
    String testOutputs[] = new String[]{"[\"x\",34.2,45.5,0.4]",
                                        "[\"y\",72.5,82.5,0.5]"};

    PAssert.that(output).containsInAnyOrder(testOutputs);
    p.run().waitUntilFinish();
  }
  
  @Test
  @Category(NeedsRunner.class)
  public void testWeatherStatsTransform() throws Exception {

    String[] testInputs = new String[]{"x,31.4,-39.2,2/2/21,4.0,7.5,0.1",
                                       "x,31.4,-39.2,2/2/21,3.5,6.0,0.3",
                                       "y,33.4,-49.2,2/2/21,12.5,17.5,0.5"};

    List<String> input = Arrays.asList(testInputs);
    PCollection<String> output =
        p.apply(Create.of(input))
         .apply(new WeatherStatsTransform());
    
    String testOutputs[] = new String[]{"[\"x\",38.3,45.5,0.4]",
                                        "[\"y\",54.5,63.5,0.5]"};

    PAssert.that(output).containsInAnyOrder(testOutputs);
    p.run().waitUntilFinish();
  }  

}
