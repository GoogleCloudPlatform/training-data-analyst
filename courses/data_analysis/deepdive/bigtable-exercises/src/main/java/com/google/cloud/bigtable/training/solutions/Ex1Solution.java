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

package com.google.cloud.bigtable.training.solutions;

import com.google.cloud.bigtable.hbase.BigtableConfiguration;
import com.google.cloud.bigtable.training.common.ThreadPoolWriter;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;
import org.apache.hadoop.hbase.HColumnDescriptor;
import org.apache.hadoop.hbase.HTableDescriptor;
import org.apache.hadoop.hbase.TableName;
import org.apache.hadoop.hbase.client.Admin;
import org.apache.hadoop.hbase.client.BufferedMutator;
import org.apache.hadoop.hbase.client.BufferedMutatorParams;
import org.apache.hadoop.hbase.client.Connection;
import org.apache.hadoop.hbase.client.Put;
import org.apache.hadoop.hbase.client.Table;
import org.apache.hadoop.hbase.util.Bytes;

/**
 * Exercise 1 - import event data into Bigtable.
 *
 * Example invocation:
 *
 * mvn compile exec:java -Dexec.mainClass=com.google.cloud.bigtable.training.Ex1 \
 *    -Dbigtable.project=<your project> \
 *    -Dbigtable.instance=<your instance> \
 *    -Dbigtable.table=<any table name> \
 *    -Dbigtable.useBufferedMutator=<true or false> \
 *    -Dexec.cleanupDaemonThreads=false
 */
public class Ex1Solution {
  public static void main(String[] args) throws Exception {
    String projectId = System.getProperty("bigtable.project");
    String instanceId = System.getProperty("bigtable.instance");
    String tableName = System.getProperty("bigtable.table");
    boolean useBufferedMutator = Boolean.getBoolean("bigtable.useBufferedMutator");

    try (Connection connection = BigtableConfiguration.connect(projectId, instanceId)) {

      CreateTable(connection, tableName);

      final Table table = connection.getTable(TableName.valueOf(tableName));

      // Set up the BufferedMutator
      BufferedMutatorParams params = new BufferedMutatorParams(TableName.valueOf(tableName))
          .listener((e, bufferedMutator) -> System.out.println(e.getMessage()));
      BufferedMutator bufferedMutator = connection.getBufferedMutator(params);

      // Initialize the ThreadPoolWriter for non-buffered writes.
      // Change the number of threads to see how things change!
      final ThreadPoolWriter writer = new ThreadPoolWriter(8);
      final AtomicInteger rowCount = new AtomicInteger();
      long startTime = System.currentTimeMillis();

      // Parse the csv file
      String[] headers = { "time", "user", "action", "item" };
      BufferedReader br = new BufferedReader(new InputStreamReader(Ex1Solution.class.getResourceAsStream("/actions_subset.csv")));
      String line;
      System.out.println("Start Importing");
      while ((line = br.readLine()) != null) {
        String[] vals = line.split(",");
        Map<String, String> rowData = new HashMap<>();
        for (int i = 0; i < 4; i++) {
          rowData.put(headers[i], vals[i]);
        }

        // Send the data as a Map into one of the write methods
        if (useBufferedMutator) {
          WriteWithBufferedMutator(bufferedMutator, rowData);
        } else {
          SinglePut(table, writer, rowData);
        }

        rowCount.incrementAndGet();
        if (rowCount.get() % 10000 == 0) {
          System.out.println(rowCount.get() + " rows imported");
          if (!useBufferedMutator) {
            // It's too slow to wait much longer.
            break;
          }
        }
      }

      writer.shutdownAndWait();

      long totalTime = System.currentTimeMillis() - startTime;
      totalTime++;
      long rps = rowCount.get() / (totalTime / 1000);
      System.out.println("You wrote " + rowCount.get() + " rows at " + rps + " rows per second");

      // TODO: Try running `cbt count <table>` to make sure the actual row count matches
    } catch (IOException e) {
      System.err.println("Exception while running Ex1: " + e.getMessage());
      e.printStackTrace();
      System.exit(1);
    }
  }

  private static void CreateTable(Connection connection, String tableName) throws Exception {
    Admin admin = connection.getAdmin();

    // Don't recreate the table, it's surprisingly slow to delete and then recreate a table with
    // the same name.
    if (admin.tableExists(TableName.valueOf(tableName))) {
      admin.truncateTable(TableName.valueOf(tableName), false);
      return;
    }

    HTableDescriptor descriptor = new HTableDescriptor(TableName.valueOf(tableName));
    descriptor.addFamily(new HColumnDescriptor("data"));
    descriptor.addFamily(new HColumnDescriptor("rollups"));

    System.out.println("Create table " + descriptor.getNameAsString());
    admin.createTable(descriptor);
  }

  // Make the row key from the record
  private static String getRowKey(Map<String, String> data) {
    String user = data.get("user").toString();
    String ts = data.get("time").toString();
    return String.join("#", "action", user, ts);
  }

  private static Put getPut(Map<String, String> data) {
    Put put = new Put(Bytes.toBytes(getRowKey(data)), Long.parseLong(data.get("time")) * 1000);
    byte[] family = Bytes.toBytes("data");

    for (String tag : data.keySet()) {
      // TODO: For each key/value pair in the map, add a column to the Put.
      put.addColumn(family, Bytes.toBytes(tag), Bytes.toBytes(data.get(tag)));
    }
    return put;
  }

  private static void SinglePut(final Table table, ThreadPoolWriter writer, Map<String, String> data) throws Exception {
    // TODO 2: For each data point, write a single row into Bigtable.
    // Experiment with the number of threads in ThreadPoolWriter to see how Bigtable scales with concurrent writes.
    writer.execute(() -> {
      table.put(getPut(data));
    }, data);
  }

  private static void WriteWithBufferedMutator(BufferedMutator bm, Map<String, String> data) throws Exception {
    // TODO 4: Add the mutation to the BufferedMutator
    bm.mutate(getPut(data));
  }
}
