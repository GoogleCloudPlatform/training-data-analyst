package com.google.cloud.bigtable.training.solutions;

import com.google.cloud.bigtable.hbase.BigtableConfiguration;
import com.google.cloud.bigtable.training.common.DataGenerator;
import com.google.cloud.bigtable.training.common.ThreadPoolWriter;
import org.apache.hadoop.hbase.HColumnDescriptor;
import org.apache.hadoop.hbase.HTableDescriptor;
import org.apache.hadoop.hbase.TableExistsException;
import org.apache.hadoop.hbase.TableName;
import org.apache.hadoop.hbase.client.*;
import org.apache.hadoop.hbase.util.Bytes;

import java.io.IOException;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Exercise 1 - write some data to Bigtable.
 *
 * Example invocation:
 *
 * mvn compile exec:java -Dexec.mainClass=com.google.cloud.bigtable.training.Ex1 \
 *    -Dbigtable.project=<your project> \
 *    -Dbigtable.instance=<your instance> \
 *    -Dbigtable.table=<any table name>
 */
public class Ex1Solution {
  public static void main(String[] args) throws Exception {
    String projectId = System.getProperty("bigtable.project");
    String instanceId = System.getProperty("bigtable.instance");
    String tableName = System.getProperty("bigtable.table");

    try (Connection connection = BigtableConfiguration.connect(projectId, instanceId)) {

      // TODO 1a: Implement CreateTable
      CreateTable(connection, tableName);

      final Table table = connection.getTable(TableName.valueOf(tableName));

      final ThreadPoolWriter writer = new ThreadPoolWriter(16);
      final AtomicInteger rowCount = new AtomicInteger();
      long startTime = System.currentTimeMillis();

      // For 1c
      ThreadLocal<List<Put>> puts = ThreadLocal.withInitial(() -> new ArrayList<>());

      // For 1d
      BufferedMutatorParams params = new BufferedMutatorParams(TableName.valueOf(tableName))
              .listener((e, bufferedMutator) -> System.out.println(e.getMessage()));
      BufferedMutator bufferedMutator = connection.getBufferedMutator(params);

      // Generate some sample data from some point in the past until now.
      // As our write method gets faster you may want to increase the duration.
      DataGenerator.consumeRandomData(Duration.ofHours(8), point -> {
        try {
          // TODO 1b: Implement SinglePut
          SinglePut(table, writer, point);

          // TODO 1c: Comment out SinglePut, implement and uncomment MultiPut.
          // Hint: We are writing with multiple threads to keep Bigtable as busy as possible.
          // Try storing the batches in a ThreadLocal and passing that as an additional parameter to MultiPut.
          // MultiPut(table, writer, point, puts);

          // TODO 1d: Comment out MultiPut, implement and uncomment WriteWithBufferedMutator.
          // You will need to create a BufferedMutator in the appropriate place and take care to close() it when finished.
          // You might want to figure out how to listen for Exceptions from the BufferedMutator for
          // debugging purposes if something goes wrong.
          // You might find this method fast enough to consume a lot more data. What about a week's worth?
          //WriteWithBufferedMutator(bufferedMutator, point);
        } catch (Exception e) {
          throw new RuntimeException(e);
        }

        rowCount.incrementAndGet();
      });


      // 1b, 1c
      writer.shutdownAndWait();

      // For 1d
      bufferedMutator.close();

      long totalTime = Math.max(1000, System.currentTimeMillis() - startTime);
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

    try {
      admin.disableTable(TableName.valueOf(tableName));
      admin.deleteTable(TableName.valueOf(tableName));
    } catch (Exception e) {
      // Ignore it, the table might not exist and we're not checking
    }

    // TODO 1a: Create a table named with the tableName variable with a column family called "data"
    // and one called "tags" programmatically using the method in Ex0.
    // Delete the table if it already exists for a clean run each time.
    // You can also delete and recreate this table using the cbt tool as needed.
    // Create a table with a single column family
    HTableDescriptor descriptor = new HTableDescriptor(TableName.valueOf(tableName));
    descriptor.addFamily(new HColumnDescriptor("data"));
    descriptor.addFamily(new HColumnDescriptor("tags"));

    System.out.println("Create table " + descriptor.getNameAsString());
    admin.createTable(descriptor);
  }

  private static String getRowKey(Map<String, Object> point) {
    String service = point.get(DataGenerator.SERVICE_ID_FIELD).toString();
    String metric = point.get(DataGenerator.METRIC_FIELD).toString();
    String ts = point.get(DataGenerator.TIMESTAMP_FIELD).toString();
    return String.join("#", service, metric, ts);
  }

  private static Put getPut(Map<String, Object> point) {
    Put put = new Put(Bytes.toBytes(getRowKey(point)));
    put.addColumn(Bytes.toBytes("data"), Bytes.toBytes("value"),
            Bytes.toBytes(point.get(DataGenerator.VALUE_FIELD).toString()));
    Map<String, String> tags = (Map<String, String>) point.get(DataGenerator.TAGS_FIELD);
    if (tags != null) {
      for (String tag : tags.keySet()) {
        put.addColumn(Bytes.toBytes("tags"), Bytes.toBytes(tag), Bytes.toBytes(tags.get(tag)));
      }
    }
    return put;
  }

  private static void SinglePut(final Table table, ThreadPoolWriter writer, Map<String, Object> point) throws Exception {
    // TODO 1b: For each data point, write a single row into Bigtable.
    // Field names are defined in DataGenerator as public constants.
    // Construct a row key out of the metric name, service and timestamp that efficiently distributes
    // the data across nodes.
    // For each wrote, write the value to column family "data", column "value".
    // Put each tag in the "tags" column family with a column named after the key in the map
    // and the corresponding map value as the cell value.
    // Catch and log any Exceptions that are thrown.
    // Experiment with the number of threads in the writer to see how Bigtable scales with concurrent writes.
    writer.execute(() -> {
      // Your code to write a row here.
      try {
        table.put(getPut(point));
      } catch (IOException e) {
        e.printStackTrace();
      }
    }, Long.parseLong(point.get(DataGenerator.TIMESTAMP_FIELD).toString()));
  }

  private static void MultiPut(final Table table, ThreadPoolWriter writer, Map<String, Object> point, ThreadLocal<List<Put>> puts)
          throws Exception {
    // TODO 1c: This time, instead of doing one Put at a time, write in batches using a List of PutsEx1.
    // Experiment with different batch sizes to see the performance differences.
    int batchSize = 10;
    writer.execute(() -> {
      puts.get().add(getPut(point));
      if (puts.get().size() == batchSize) {
        try {
          table.put(puts.get());
        } catch (IOException e) {
          e.printStackTrace();
        }
        puts.get().clear();
      }
    }, Long.parseLong(point.get(DataGenerator.TIMESTAMP_FIELD).toString()));
  }

  private static void WriteWithBufferedMutator(BufferedMutator bm, Map<String, Object> point) throws Exception {
    bm.mutate(getPut(point));
  }
}
