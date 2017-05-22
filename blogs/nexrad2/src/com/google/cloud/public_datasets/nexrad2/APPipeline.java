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
package com.google.cloud.public_datasets.nexrad2;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import org.apache.beam.runners.dataflow.DataflowRunner;
import org.apache.beam.runners.dataflow.options.DataflowPipelineOptions;
import org.apache.beam.sdk.Pipeline;
import org.apache.beam.sdk.coders.StringUtf8Coder;
import org.apache.beam.sdk.io.TextIO;
import org.apache.beam.sdk.options.Default;
import org.apache.beam.sdk.options.Description;
import org.apache.beam.sdk.options.PipelineOptionsFactory;
import org.apache.beam.sdk.transforms.Create;
import org.apache.beam.sdk.transforms.DoFn;
import org.apache.beam.sdk.transforms.ParDo;
import org.apache.beam.sdk.transforms.Sum;
import org.apache.beam.sdk.values.KV;
import org.apache.beam.sdk.values.PCollection;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.google.cloud.public_datasets.nexrad2.APDetector.AnomalousPropagation;

import ucar.nc2.dt.RadialDatasetSweep;

/**
 * Scales out the APDetector to a large number of volume scans
 * 
 * @author vlakshmanan
 *
 */
public class APPipeline {
  private static final Logger log = LoggerFactory.getLogger(APPipeline.class);
  
  public static int[] YEARS  = { 2012, 2013, 2014 };
  public static int[] MONTHS = { 6, 7, 8 };

  public static interface MyOptions extends DataflowPipelineOptions {
    @Description("Output directory")
    @Default.String("gs://cloud-training-demos-ml/nexrad/")
    String getOutput();

    void setOutput(String s);

    @Description("radars to process")
    @Default.String("KYUX,KIWA,KFSX")
    String getRadars();

    void setRadars(String s);
  }

  @SuppressWarnings("serial")
  public static void main(String[] args) {
    MyOptions options = PipelineOptionsFactory.fromArgs(args).withValidation().as(MyOptions.class);
    options.setRunner(DataflowRunner.class);
    options.setTempLocation(options.getOutput() + "staging");
    Pipeline p = Pipeline.create(options);
    
    // now use Dataflow to process them all in parallel
    // GCP will scale out the processing
    PCollection<APDetector.AnomalousPropagation> ap = p//
        .apply("getRadars", Create.of(getRadars(options)).withCoder(StringUtf8Coder.of())) //
        .apply("getArchives", ParDo.of(new DoFn<String, String>() {
          @ProcessElement
          public void processElement(ProcessContext c) throws Exception {
            String radar = c.element();
            for (int year : YEARS) {
              for (int month : MONTHS) {
                List<String> files = GcsNexradL2List.getFiles(radar, year, month);
                log.info(files.size() + " files for " + radar + " " + year + " " + month);
                for (String file : files) {
                  c.output(file);
                }
              }
            }
          }
        }))
        .apply("processTar", ParDo.of(new DoFn<String, AnomalousPropagation>() {
          @ProcessElement
          public void processElement(ProcessContext c) throws Exception {
            String tarFile = c.element();
            try (GcsNexradL2Read hourly = new GcsNexradL2Read(tarFile)) {
              for (RadialDatasetSweep volume : hourly.getVolumeScans()) {
                List<AnomalousPropagation> apPixels = APDetector.findAP(volume);
                log.info("Found " + apPixels.size() + " AP pixels");
                for (AnomalousPropagation ap : apPixels) {
                  c.output(ap);
                }
              }
            }
          }
        }));

    // write out all the detections
    ap.apply("AP->String", ParDo.of(new DoFn<AnomalousPropagation, String>() {
      @ProcessElement
      public void processElement(ProcessContext c) throws Exception {
        AnomalousPropagation ap = c.element();
        c.output(ap.toString());
      }
    }))//
        .apply("writeAll", TextIO.Write.to(options.getOutput() + "allDetections").withSuffix(".csv"));

    // let's also find the total problems by radar
    ap.apply("ByRadar", ParDo.of(new DoFn<AnomalousPropagation, KV<String, Integer>>() {
      @ProcessElement
      public void processElement(ProcessContext c) throws Exception {
        AnomalousPropagation ap = c.element();
        c.output(KV.of(ap.radarId, 1)); // once for each pixel with AP
      }
    }))//
        .apply("TotalAP", Sum.integersPerKey()) //
        .apply("KV->String", ParDo.of(new DoFn<KV<String, Integer>, String>() {
          @ProcessElement
          public void processElement(ProcessContext c) throws Exception {
            String radar = c.element().getKey();
            int numPixelsAP = c.element().getValue();
            c.output(radar + "," + numPixelsAP);
          }
        }))//
        .apply("writeTotalByRadar", TextIO.Write.to(options.getOutput() + "totalByRadar")//
            .withSuffix(".csv").withoutSharding());
    
    // run the graph
    p.run();
  }

  private static List<String> getRadars(MyOptions options) {
    String[] radars = options.getRadars().split(",");
    return Arrays.asList(radars);
  }
}
