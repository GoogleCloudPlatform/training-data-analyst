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

import com.google.cloud.bigtable.hbase.BigtableConfiguration;
import com.google.cloud.bigtable.training.common.DataGenerator;
import com.google.cloud.bigtable.training.common.ThreadPoolWriter;
import com.google.common.util.concurrent.MoreExecutors;
import java.io.IOException;
import java.time.Duration;
import java.util.Date;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.RejectedExecutionHandler;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import org.apache.hadoop.hbase.HColumnDescriptor;
import org.apache.hadoop.hbase.HTableDescriptor;
import org.apache.hadoop.hbase.TableExistsException;
import org.apache.hadoop.hbase.TableName;
import org.apache.hadoop.hbase.client.Admin;
import org.apache.hadoop.hbase.client.Connection;
import org.apache.hadoop.hbase.client.Get;
import org.apache.hadoop.hbase.client.Put;
import org.apache.hadoop.hbase.client.Result;
import org.apache.hadoop.hbase.client.Table;
import org.apache.hadoop.hbase.util.Bytes;


/**
 * This just makes sure you can compile and run a trivial program that reads and writes to bigtable
 */
public class Ex0 {

  public static void main(String[] args) {
    String projectId = System.getProperty("bigtable.project");
    String instanceId = System.getProperty("bigtable.instance");
    String tableName = System.getProperty("bigtable.table");
    try (Connection connection = BigtableConfiguration.connect(projectId, instanceId)) {
      // The admin API lets us create, manage and delete tables
      Admin admin = connection.getAdmin();

      // Create a table with a single column family
      HTableDescriptor descriptor = new HTableDescriptor(TableName.valueOf(tableName));
      descriptor.addFamily(new HColumnDescriptor("cf"));

      System.out.println("Create table " + descriptor.getNameAsString());
      try {
        admin.createTable(descriptor);
      } catch (TableExistsException e) {
        // No problem!
      }

      Table table = connection.getTable(TableName.valueOf(tableName));

      // Write something
      Put put = new Put(Bytes.toBytes("row"));
      put.addColumn(Bytes.toBytes("cf"), Bytes.toBytes("col"),
          Bytes.toBytes("It worked!"));
      table.put(put);

      // Now read it back
      Result getResult = table.get(new Get(Bytes.toBytes("row")));
      String val =
          Bytes.toString(getResult.getValue(Bytes.toBytes("cf"), Bytes.toBytes("col")));
      System.out.println(val);
      System.exit(0);
    } catch (IOException e) {
      System.err.println("Exception while running Ex0: " + e.getMessage());
      e.printStackTrace();
      System.exit(1);
    }
  }
}
