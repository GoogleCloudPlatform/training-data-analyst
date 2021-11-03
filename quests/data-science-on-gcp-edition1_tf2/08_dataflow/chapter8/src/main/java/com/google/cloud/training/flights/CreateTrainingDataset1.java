/*
 * Copyright (C) 2017 Google Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not
 * use this file except in compliance with the License. You may obtain a copy of
 * the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations under
 * the License.
 */

package com.google.cloud.training.flights;

import java.util.Arrays;

import org.apache.beam.sdk.Pipeline;
import org.apache.beam.sdk.options.PipelineOptionsFactory;
import org.apache.beam.sdk.transforms.Create;
import org.apache.beam.sdk.transforms.DoFn;
import org.apache.beam.sdk.transforms.ParDo;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * A dataflow pipeline that demonstrates filtering.
 * 
 * @author vlakshmanan
 *
 */
public class CreateTrainingDataset1 {
  private static final Logger LOG = LoggerFactory.getLogger(CreateTrainingDataset1.class);

  @SuppressWarnings("serial")
  public static void main(String[] args) {
    Pipeline p = Pipeline.create(PipelineOptionsFactory.fromArgs(args).withValidation().create());

    String[] events = {
        "2015-09-20,AA,19805,AA,1572,13303,1330303,32467,MIA,12889,1288903,32211,LAS,2015-09-20T22:50:00,2015-09-20T04:03:00,313.00,19.00,2015-09-20T04:22:00,,,2015-09-21T04:08:00,,,0.00,,,2174.00,25.79527778,-80.29000000,-14400.0,36.08000000,-115.15222222,-25200.0,wheelsoff,2015-09-20T04:22:00",
        "2015-09-20,AA,19805,AA,2495,11298,1129804,30194,DFW,12892,1289203,32575,LAX,2015-09-21T01:25:00,2015-09-20T06:04:00,279.00,15.00,2015-09-20T06:19:00,,,2015-09-21T04:55:00,,,0.00,,,1235.00,32.89722222,-97.03777778,-18000.0,33.94250000,-118.40805556,-25200.0,wheelsoff,2015-09-20T06:19:00",
        "2015-09-20,AA,19805,AA,2342,11292,1129202,30325,DEN,13303,1330303,32467,MIA,2015-09-21T05:59:00,2015-09-20T06:33:00,34.00,14.00,2015-09-20T06:47:00,,,2015-09-20T09:47:00,,,0.00,,,1709.00,39.86166667,-104.67305556,-21600.0,25.79527778,-80.29000000,-14400.0,wheelsoff,2015-09-20T06:47:00" };

    p //
        .apply(Create.of(Arrays.asList(events))) //
        .apply(ParDo.of(new DoFn<String, String>() {
          @ProcessElement
          public void processElement(ProcessContext c) throws Exception {
            String input = c.element();
            if (input.contains("MIA")) {
              c.output(input);
            }
          }
        })) //
        .apply(ParDo.of(new DoFn<String, Void>() {
          @ProcessElement
          public void processElement(ProcessContext c) {
            LOG.info(c.element());
          }
        }));

    p.run();
  }
}
