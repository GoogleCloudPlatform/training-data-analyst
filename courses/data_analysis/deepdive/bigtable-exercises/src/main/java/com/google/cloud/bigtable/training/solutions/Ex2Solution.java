package com.google.cloud.bigtable.training.solutions;

import com.google.cloud.bigtable.hbase.BigtableConfiguration;
import org.apache.hadoop.hbase.TableName;
import org.apache.hadoop.hbase.client.*;
import org.apache.hadoop.hbase.filter.BinaryComparator;
import org.apache.hadoop.hbase.filter.CompareFilter;
import org.apache.hadoop.hbase.filter.SingleColumnValueFilter;
import org.apache.hadoop.hbase.util.Bytes;

import java.io.IOException;

/**
 * Exercise 2 - A command-line tool to read monitoring data from Bigtable.
 * <p>
 * Example:
 */
public class Ex2Solution {
    public enum Function {
        SUM,
        AVG, // Note: This is a 1-minute average
        MAX
    }

    public static void main(String[] args) throws Exception {
        String projectId = System.getProperty("bigtable.project");
        String instanceId = System.getProperty("bigtable.instance");
        String tableName = System.getProperty("bigtable.table");

        if (args.length < 5) {
            System.err.println("Invalid comamand. Usage:");
            System.err.println("Ex2 <service> <metric> <avg|sum|max> <start timestamp> <end timestamp|now>");
            System.exit(1);
        }

        String service = args[0];
        String metric = args[1];
        String functionName = args[2].toLowerCase();
        Function function = null;
        switch (functionName) {
            case "sum":
                function = Function.SUM;
                break;
            case "avg":
                function = Function.AVG;
                break;
            case "max":
                function = Function.MAX;
                break;
            default:
                System.err.println("Invalid function: " + functionName);
                System.exit(1);
        }

        // Try from 0 to "now" to avoid looking up timestamps
        long from = Long.parseLong(args[3]);
        long to = args[4].equalsIgnoreCase("now") ? System.currentTimeMillis() : Long.parseLong(args[4]);

        try (Connection connection = BigtableConfiguration.connect(projectId, instanceId)) {
            Table table = connection.getTable(TableName.valueOf(tableName));

            doQuery(table, service, metric, function, from, to);

        } catch (IOException e) {
            System.err.println("Exception while running Ex2: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }
    }

    /**
     * @param table     the table to query
     * @param service   the service id
     * @param metric    the metric id
     * @param function  the function to apply to the returned data
     * @param startTime the (inclusive) starting timestamp
     * @param endTime   the (exclusive) ending timestamp
     */
    private static void doQuery(Table table, String service, String metric, Function function,
                                long startTime, long endTime) throws Exception {
        // TODO: Your code here.
        // Query the table for the data as described.
        String startRowKey = service + "#" + metric + "#" + startTime;
        String endRowKey = service + "#" + metric + "#" + endTime;

        Scan scan = new Scan();
        scan.setStartRow(Bytes.toBytes(startRowKey));
        scan.setStopRow(Bytes.toBytes(endRowKey));

        ResultScanner scanner = table.getScanner(scan);
        try {
            double total = 0;
            int rows = 0;
            double max = Double.MIN_VALUE;
            for (Result r = scanner.next(); r != null; r = scanner.next()) {
                double value = Double.parseDouble(Bytes.toString(r.getValue(Bytes.toBytes("data"), Bytes.toBytes("value"))));
                System.out.println(new String(r.getRow()) + " " + value);
                rows++;
                switch (function) {
                    case AVG:
                    case SUM:
                        total += value;
                        break;
                    case MAX:
                        max = Math.max(max, value);
                        break;
                }
            }

            switch (function) {
                case AVG:
                    System.out.println("The avg is " + total / rows);
                    break;
                case SUM:
                    System.out.println("The sum is " + total);
                    break;
                case MAX:
                    System.out.println("The max is " + max);
                    break;
            }
        } finally {
            scanner.close();
        }
    }
}
