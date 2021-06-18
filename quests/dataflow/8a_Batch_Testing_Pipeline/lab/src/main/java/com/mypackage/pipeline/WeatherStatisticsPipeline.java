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

import com.google.gson.Gson;
import org.apache.beam.sdk.options.PipelineOptions;
import org.apache.beam.sdk.Pipeline;
import org.apache.beam.sdk.PipelineResult;
import org.apache.beam.sdk.extensions.jackson.AsJsons;
import org.apache.beam.sdk.io.TextIO;
import org.apache.beam.sdk.options.Description;
import org.apache.beam.sdk.options.PipelineOptionsFactory;
import org.apache.beam.sdk.schemas.transforms.Group;
import org.apache.beam.sdk.schemas.transforms.Select;
import org.apache.beam.sdk.transforms.*;
import org.apache.beam.sdk.transforms.DoFn.ProcessElement;
import org.apache.beam.sdk.values.PCollection;
import org.apache.beam.sdk.values.Row;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;


public class WeatherStatisticsPipeline {

    /**
     * The logger to output status messages to.
     */
    private static final Logger LOG = LoggerFactory.getLogger(WeatherStatisticsPipeline.class);

    /**
     * The {@link Options} class provides the custom execution options passed by the
     * executor at the command-line.
     */

    public interface Options extends PipelineOptions {
        @Description("Path to records.csv")
        String getInputPath();
        void setInputPath(String inputPath);

        @Description("Output prefix name")
        String getOutputPrefix();
        void setOutputPrefix(String outputPrefix);
    }


    /**
     * DoFn to parse incoming CSV rows (comma-delimited) into objects of type WeatherRecord
     * 
     */

    public static class ConvertCsvToWeatherRecord extends DoFn<String, WeatherRecord> {
        @ProcessElement
		public void processElement(@Element String line, OutputReceiver<WeatherRecord> o) throws Exception {
            String[] rowValues = line.split(",");
            String locId = rowValues[0];
            Double lat = Double.parseDouble(rowValues[1]);
            Double lng = Double.parseDouble(rowValues[2]);
            String date = rowValues[3];
            Double lowTemp = Double.parseDouble(rowValues[4]);
            Double highTemp = Double.parseDouble(rowValues[5]);
            Double precip = Double.parseDouble(rowValues[6]);
            WeatherRecord record = new WeatherRecord(locId, lat, lng, date, lowTemp, highTemp, precip);
            o.output(record);
        }
    }

    public static class ConvertTempUnits extends DoFn<WeatherRecord, WeatherRecord> {
       @ProcessElement
        public void processElement(@Element WeatherRecord record,
                                   OutputReceiver<WeatherRecord> o) throws Exception {
            Double lowTempF = record.lowTemp * 1.8 + 32.0;
            Double highTempF = record.highTemp * 1.8 + 31.0;
            WeatherRecord recordF = new WeatherRecord(record.locId, record.lat, record.lng, record.date, lowTempF, highTempF, record.precip);
            o.output(recordF);
        }
    }

    public static class ConvertToJson extends DoFn<Row, String> {
        @ProcessElement
        public void processElement(@Element Row row,
                                    OutputReceiver<String> o) throws Exception {
            Gson g = new Gson();
            String json = g.toJson(row.getValues());
            o.output(json);                            

                                    }
    }

    public static class ComputeStatistics extends PTransform<PCollection<WeatherRecord>, PCollection<String>>{

        @Override
        public PCollection<String> expand(PCollection<WeatherRecord> pcoll){

            PCollection<String> weatherStats = 
                pcoll.apply("Aggregations", Group.<WeatherRecord>byFieldNames("locId")
                        .aggregateField("lowTemp", Min.ofDoubles(), "recordLow")
                        .aggregateField("highTemp", Max.ofDoubles(), "recordHigh")
                        .aggregateField("precip", Sum.ofDoubles(), "totalPrecip"))
                     .apply("UnnestFields", Select.fieldNames("key.locId", 
                                                         "value.recordLow",
                                                         "value.recordHigh",
                                                         "value.totalPrecip"))
                     .apply("ToJson", ParDo.of(new ConvertToJson()));

            return weatherStats;
        }
    }

    public static class WeatherStatsTransform extends PTransform<PCollection<String>, PCollection<String>> {

        @Override
        public PCollection<String> expand(PCollection<String> pcoll)
        {
            PCollection<String> weatherStats =
                pcoll.apply("ParseCSV", ParDo.of(new ConvertCsvToWeatherRecord()))
                     .apply("ConvertCelToFar", ParDo.of(new ConvertTempUnits()))
                     .apply("ComputeStatistics", new ComputeStatistics());

            return weatherStats;
        }
    }


    /**
     * The main entry-point for pipeline execution. This method will start the
     * pipeline but will not wait for it's execution to finish. If blocking
     * execution is required, use the {@link BatchUserTrafficPipeline#run(Options)} method to
     * start the pipeline and invoke {@code result.waitUntilFinish()} on the
     * {@link PipelineResult}.
     *
     * @param args The command-line args passed by the executor.
     */
    public static void main(String[] args) {
        Options options = PipelineOptionsFactory.fromArgs(args).withValidation().as(Options.class);

        run(options);
    }

    /**
     * Runs the pipeline to completion with the specified options. This method does
     * not wait until the pipeline is finished before returning. Invoke
     * {@code result.waitUntilFinish()} on the result object to block until the
     * pipeline is finished running if blocking programmatic execution is required.
     *
     * @param options The execution options.
     * @return The pipeline result.
     */

    public static PipelineResult run(Options options) {

        // Create the pipeline
        Pipeline pipeline = Pipeline.create(options);
        options.setJobName("weather-stats-pipeline-" + System.currentTimeMillis());

        /*
         * Steps:
         * 1) Read something
         * 2) Transform something
         * 3) Write something
         */

        pipeline
                // Read in lines from GCS and Parse to WeatherRecord
                .apply("ReadFromText", TextIO.read().from(options.getInputPath()))
                .apply("WeatherStatistics", new WeatherStatsTransform())                                                                                              
                .apply("WriteToText", TextIO.write().to(options.getOutputPrefix()).withSuffix(".json"));

        LOG.info("Building pipeline...");

        return pipeline.run();
    }
}