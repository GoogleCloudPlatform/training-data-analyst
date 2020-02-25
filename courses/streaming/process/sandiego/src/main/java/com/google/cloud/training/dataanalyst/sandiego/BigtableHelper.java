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
package com.google.cloud.training.dataanalyst.sandiego;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

import org.apache.beam.runners.dataflow.options.DataflowPipelineOptions;
import org.apache.beam.sdk.io.gcp.bigtable.BigtableIO;
import org.apache.beam.sdk.extensions.gcp.options.GcpOptions;
import org.apache.beam.sdk.transforms.DoFn;
import org.apache.beam.sdk.transforms.ParDo;
import org.apache.beam.sdk.values.KV;
import org.apache.beam.sdk.values.PCollection;
import org.joda.time.DateTime;
import org.joda.time.format.DateTimeFormat;
import org.joda.time.format.DateTimeFormatter;

import com.google.bigtable.admin.v2.ColumnFamily;
import com.google.bigtable.admin.v2.CreateTableRequest;
import com.google.bigtable.admin.v2.GetTableRequest;
import com.google.bigtable.admin.v2.Table;
import com.google.bigtable.v2.Mutation;
import com.google.cloud.bigtable.config.BigtableOptions;
import com.google.cloud.bigtable.config.BigtableOptions.Builder;
import com.google.cloud.bigtable.config.BulkOptions;
import com.google.cloud.bigtable.config.CredentialOptions;
import com.google.cloud.bigtable.grpc.BigtableSession;
import com.google.cloud.bigtable.grpc.BigtableTableAdminClient;
import com.google.protobuf.ByteString;

/**
 * Helper class to stream a PCollection<LaneInfo> to Bigtable
 * 
 * @author vlakshmanan
 *
 */
@SuppressWarnings("serial")
public class BigtableHelper {

  private final static String INSTANCE_ID = "sandiego";
  private final static String TABLE_ID    = "current_conditions";
  private final static String CF_FAMILY   = "lane";

  public static void writeToBigtable(PCollection<LaneInfo> laneInfo, DataflowPipelineOptions options) {
    BigtableOptions.Builder optionsBuilder = //
        new BigtableOptions.Builder()//
            .setProjectId(options.getProject()) //
            .setInstanceId(INSTANCE_ID).setUserAgent("cpb210");
    
    // batch up requests to Bigtable every 100ms, although this can be changed
    // by specifying a lower/higher value for BIGTABLE_BULK_THROTTLE_TARGET_MS_DEFAULT
    BulkOptions bulkOptions = new BulkOptions.Builder().enableBulkMutationThrottling().build();
    optionsBuilder = optionsBuilder.setBulkOptions(bulkOptions);
    
    createEmptyTable(options, optionsBuilder);
    PCollection<KV<ByteString, Iterable<Mutation>>> mutations = toMutations(laneInfo);
    mutations.apply("write:cbt", //
        BigtableIO.write().withBigtableOptions(optionsBuilder.build()).withTableId(TABLE_ID));
  }

  private static void createEmptyTable(DataflowPipelineOptions options, Builder optionsBuilder) {
    Table.Builder tableBuilder = Table.newBuilder();
    ColumnFamily cf = ColumnFamily.newBuilder().build();
    tableBuilder.putColumnFamilies(CF_FAMILY, cf);

    try (BigtableSession session = new BigtableSession(optionsBuilder
        .setCredentialOptions(CredentialOptions.credential(options.as(GcpOptions.class).getGcpCredential())).build())) {
      BigtableTableAdminClient tableAdminClient = session.getTableAdminClient();

      try {
        // if get fails, then create
        String tableName = getTableName(options);
        GetTableRequest.Builder getTableRequestBuilder = GetTableRequest.newBuilder().setName(tableName);
        tableAdminClient.getTable(getTableRequestBuilder.build());
      } catch (Exception e) {
        CreateTableRequest.Builder createTableRequestBuilder = //
            CreateTableRequest.newBuilder().setParent(getInstanceName(options)) //
                .setTableId(TABLE_ID).setTable(tableBuilder.build());
        tableAdminClient.createTable(createTableRequestBuilder.build());
      }

    } catch (IOException e) {
      throw new RuntimeException(e);
    }
  }

  private static DateTimeFormatter fmt = DateTimeFormat.forPattern("yyyy-MM-dd HH:mm:ss");

  private static PCollection<KV<ByteString, Iterable<Mutation>>> toMutations(PCollection<LaneInfo> laneInfo) {
    return laneInfo.apply("pred->mutation", ParDo.of(new DoFn<LaneInfo, KV<ByteString, Iterable<Mutation>>>() {
      @ProcessElement
      public void processElement(ProcessContext c) throws Exception {
        LaneInfo info = c.element();
        DateTime ts = fmt.parseDateTime(info.getTimestamp().replace('T', ' '));

        // key is HIGHWAY#DIR#LANE#REVTS
        String key = info.getHighway() //
            + "#" + info.getDirection() //
            + "#" + info.getLane() //
            + "#" + (Long.MAX_VALUE - ts.getMillis()); // reverse time stamp

        // all the data is in a wide column table with only one column family
        List<Mutation> mutations = new ArrayList<>();
        addCell(mutations, "timestamp", info.getTimestamp(), ts.getMillis());
        addCell(mutations, "latitude", info.getLatitude(), ts.getMillis());
        addCell(mutations, "longitude", info.getLongitude(), ts.getMillis());
        addCell(mutations, "highway", info.getHighway(), ts.getMillis());
        addCell(mutations, "direction", info.getDirection(), ts.getMillis());
        addCell(mutations, "lane", info.getLane(), ts.getMillis());
        addCell(mutations, "speed", info.getSpeed(), ts.getMillis());
        addCell(mutations, "sensorId", info.getSensorKey(), ts.getMillis());
        c.output(KV.of(ByteString.copyFromUtf8(key), mutations));
      }

    }));
  }

  private static void addCell(List<Mutation> mutations, String cellName, double cellValue, long ts) {
    addCell(mutations, cellName, Double.toString(cellValue), ts);
  }

  private static void addCell(List<Mutation> mutations, String cellName, String cellValue, long ts) {
    if (cellValue.length() > 0) {
      ByteString value = ByteString.copyFromUtf8(cellValue);
      ByteString colname = ByteString.copyFromUtf8(cellName);
      Mutation m = //
          Mutation.newBuilder()
              .setSetCell(//
                  Mutation.SetCell.newBuilder() //
                      .setValue(value)//
                      .setFamilyName(CF_FAMILY)//
                      .setColumnQualifier(colname)//
                      .setTimestampMicros(ts) //
              ).build();
      mutations.add(m);
    }
  }

  private static String getInstanceName(DataflowPipelineOptions options) {
    return String.format("projects/%s/instances/%s", options.getProject(), INSTANCE_ID);
  }

  private static String getTableName(DataflowPipelineOptions options) {
    return String.format("%s/tables/%s", getInstanceName(options), TABLE_ID);
  }
}
