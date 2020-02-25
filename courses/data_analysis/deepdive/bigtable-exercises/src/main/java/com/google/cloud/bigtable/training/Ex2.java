// Copyright 2017 Google Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
////////////////////////////////////////////////////////////////////////////////

package com.google.cloud.bigtable.training;

import com.google.cloud.bigtable.dataflow.CloudBigtableIO;
import com.google.cloud.bigtable.dataflow.CloudBigtableOptions;
import com.google.cloud.bigtable.dataflow.CloudBigtableScanConfiguration;
import com.google.cloud.bigtable.dataflow.CloudBigtableTableConfiguration;
import com.google.cloud.bigtable.training.solutions.Ex2Solution;
import com.google.cloud.dataflow.sdk.Pipeline;
import com.google.cloud.dataflow.sdk.io.Read;
import com.google.cloud.dataflow.sdk.options.PipelineOptionsFactory;
import com.google.cloud.dataflow.sdk.transforms.Count;
import com.google.cloud.dataflow.sdk.transforms.DoFn;
import com.google.cloud.dataflow.sdk.transforms.ParDo;
import com.google.cloud.dataflow.sdk.transforms.windowing.FixedWindows;
import com.google.cloud.dataflow.sdk.transforms.windowing.Window;
import com.google.cloud.dataflow.sdk.values.KV;
import com.google.cloud.dataflow.sdk.values.PCollection;
import org.apache.hadoop.hbase.client.Mutation;

import org.apache.hadoop.hbase.client.Put;
import org.apache.hadoop.hbase.client.Result;
import org.apache.hadoop.hbase.client.Scan;
import org.apache.hadoop.hbase.util.Bytes;
import org.joda.time.DateTime;
import org.joda.time.Duration;
import org.joda.time.Instant;

/**
 * Write a simple dataflow job that reads data from Bigtable, counts actions per minute,
 * and writes the counts back into bigtable.
 *
 --project=PROJECT
 --bigtableProjectId=PROJECT
 --bigtableInstanceId=INSTANCE
 --bigtableTableId=TABLE FROM PREVIOUS EXERCISE
 --runner=BlockingDataflowPipelineRunner
 --stagingLocation=STAGING AREA
 --inputFile=gs://cloud-bigtable-training/actions_subset.csv
 */

public class Ex2 {

  static class ExtractItemTimestamp extends DoFn<Result, String> {
    @Override
    public void processElement(ProcessContext c) {
      c.outputWithTimestamp("elem", new Instant(c.element().rawCells()[0].getTimestamp()));
    }
  }

  static class PersistAggregation extends DoFn<KV<String, Long>, Mutation> {

    @Override
    public void processElement(ProcessContext c) {
      long count = c.element().getValue();
      Instant timestamp = c.timestamp();
      DateTime hour = timestamp.toDateTime().hourOfDay().roundFloorCopy();

      Put put = new Put(Bytes.toBytes("hourly#" + Long.toString(hour.toInstant().getMillis())),
          timestamp.getMillis());
      byte[] family = Bytes.toBytes("rollups");

      // Put everything in one column. Data will be sorted within this column by timestamp
      // which is what we want!
      // Note that to keep all these values around indefinitely we would need to adjust the
      // GC policy on this column family using the cbt tool.
      put.addColumn(family, Bytes.toBytes(""), Bytes.toBytes(Long.toString(count)));
      c.output(put);
    }
  }

  public interface BigtableCsvOptions extends CloudBigtableOptions {

    String getInputFile();

    void setInputFile(String location);
  }


  public static void main(String[] args) {
    Ex2Solution.BigtableCsvOptions options =
        PipelineOptionsFactory.fromArgs(args).withValidation().as(Ex2Solution.BigtableCsvOptions.class);
    CloudBigtableTableConfiguration config =
        CloudBigtableTableConfiguration.fromCBTOptions(options);

    Scan scan = new Scan();
    // TODO: Do a scan of rows being with "action"

    CloudBigtableScanConfiguration scanConfiguration =
        new CloudBigtableScanConfiguration.Builder()
            .withProjectId(options.getBigtableProjectId())
            .withInstanceId(options.getBigtableInstanceId())
            .withTableId(options.getBigtableTableId())
            .withScan(scan)
            .build();

    Pipeline p = Pipeline.create(options);

    CloudBigtableIO.initializeForWrite(p);

    PCollection<String> windowedItems = p.apply(Read.from(CloudBigtableIO.read(scanConfiguration)))
        .apply(ParDo.of(new Ex2.ExtractItemTimestamp()))
        .apply(
            Window.into(FixedWindows.of(Duration.standardMinutes(1))));
    PCollection<KV<String, Long>> itemsPerMinute = windowedItems.apply(Count.perElement());

    PCollection<Mutation> mutations = itemsPerMinute.apply(ParDo.of(new Ex2.PersistAggregation()));
    mutations.apply(CloudBigtableIO.writeToTable(config));

    // Run the pipeline.
    p.run();
  }
}