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

import java.time.YearMonth;
import java.util.ArrayList;
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
import org.apache.beam.sdk.transforms.GroupByKey;
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

  public static interface MyOptions extends DataflowPipelineOptions {
    @Description("Output directory")
    @Default.String("gs://cloud-training-demos-ml/nexrad/")
    String getOutput();

    void setOutput(String s);

    @Description("comma-separated radars to process")
    @Default.String("KYUX")
    String getRadars();

    void setRadars(String s);

    @Description("comma-separated years to process")
    @Default.String("2012")
    String getYears();

    void setYears(String s);

    @Description("comma-separated months to process -- empty implies all")
    @Default.String("7")
    String getMonths();

    void setMonths(String s);

    @Description("comma-separated days to process -- empty implies all")
    @Default.String("23")
    String getDays();

    void setDays(String s);
  }

  @SuppressWarnings("serial")
  public static void main(String[] args) {
    MyOptions options = PipelineOptionsFactory.fromArgs(args).withValidation().as(MyOptions.class);
    options.setRunner(DataflowRunner.class);
    options.setTempLocation(options.getOutput() + "staging");
    Pipeline p = Pipeline.create(options);

    // now use Dataflow to process them all in parallel
    // GCP will scale out the processing
    PCollection<String> tars = p//
        .apply("getParams", Create.of(getTarNameParams(options)).withCoder(StringUtf8Coder.of())) //
        .apply("getArchives", ParDo.of(new DoFn<String, String>() {
          @ProcessElement
          public void processElement(ProcessContext c) throws Exception {
            String[] params = c.element().split(",");
            String radar = params[0];
            int year = Integer.parseInt(params[1]);
            int month = Integer.parseInt(params[2]);
            int day = Integer.parseInt(params[3]);
            List<String> files = GcsNexradL2List.getFiles(radar, year, month, day);
            log.info(files.size() + " files for " + radar + " " + year + "-" + month + "-" + day);
            for (String file : files) {
              c.output(file);
            }
          }
        }));

    tars = rebundle("rebundle", tars, 1000);

    PCollection<APDetector.AnomalousPropagation> ap = tars//
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
            } catch (Exception e) {
              log.error("Skipping " + tarFile, e);
            }
          }
        }));

    // write out all the detections
    ap.apply("AP->String", ParDo.of(new DoFn<AnomalousPropagation, String>() {
      @ProcessElement
      public void processElement(ProcessContext c) throws Exception {
        AnomalousPropagation ap = c.element();
        c.output(ap.toCsv());
      }
    }))//
        .apply("writeAll", TextIO.write().to(options.getOutput() + "allDetections").withSuffix(".csv"));

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
        .apply("writeTotalByRadar", TextIO.write().to(options.getOutput() + "totalByRadar")//
            .withSuffix(".csv").withoutSharding());

    // run the graph
    p.run();
  }

  /**
   * Rebundling improves parallelism. Each worker in Apache Beam works on only one bundle,
   * so if the number of bundles < # of potential workers, you will have limited parallelism.
   * If that's case, use this rebundle utility
   * 
   * @param name of rebundling transforms
   * @param inputs the collection to rebundle
   * @param nbundles number of bundles
   * @return
   */
  @SuppressWarnings("serial")
  private static <T> PCollection<T> rebundle(String name, PCollection<T> inputs, int nbundles) {
    return inputs//
        .apply(name + "-1", ParDo.of(new DoFn<T, KV<Integer, T>>() {
          @ProcessElement
          public void processElement(ProcessContext c) throws Exception {
            T input = c.element();
            Integer key = (int) (Math.random() * nbundles);
            c.output(KV.of(key, input));
          }
        })) //
        .apply(name + "-2", GroupByKey.<Integer, T> create())
        .apply(name + "-3", ParDo.of(new DoFn<KV<Integer, Iterable<T>>, T>() {
          @ProcessElement
          public void processElement(ProcessContext c) throws Exception {
            for (T item : c.element().getValue()) {
              c.output(item);
            }
          }
        }));
  }

  private static List<String> getTarNameParams(MyOptions options) {
    // parse command-line options
    String[] radars = options.getRadars().split(",");
    int[] years = toIntArray(options.getYears().split(","));
    int[] months = toIntArray(options.getMonths().split(","));
    if (months.length == 0) {
      // all months
      months = new int[12];
      for (int i = 1; i <= 12; ++i) {
        months[i] = i;
      }
    }
    int[] days = toIntArray(options.getDays().split(","));

    // generate parameter options
    List<String> params = new ArrayList<>();
    for (String radar : radars) {
      for (int year : years) {
        for (int month : months) {
          YearMonth yearMonthObject = YearMonth.of(year, month);
          int maxday = yearMonthObject.lengthOfMonth();
          if (days.length == 0) {
            for (int day = 1; day <= maxday; ++day) {
              params.add(radar + "," + year + "," + month + "," + day);
            }
          } else {
            for (int day : days) {
              if (day >= 1 && day <= maxday) {
                params.add(radar + "," + year + "," + month + "," + day);
              }
            }
          }
        }
      }
    }
    return params;
  }

  private static int[] toIntArray(String[] s) {
    int[] result = new int[s.length];
    for (int i = 0; i < result.length; ++i) {
      result[i] = Integer.parseInt(s[i]);
    }
    return result;
  }
}
