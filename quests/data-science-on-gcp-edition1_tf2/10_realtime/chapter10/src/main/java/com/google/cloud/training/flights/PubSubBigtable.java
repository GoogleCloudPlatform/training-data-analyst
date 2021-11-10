package com.google.cloud.training.flights;

import java.io.IOException;
import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.List;

import org.apache.beam.sdk.extensions.gcp.options.GcpOptions;
import org.apache.beam.sdk.io.gcp.bigtable.BigtableIO;
import org.apache.beam.sdk.transforms.DoFn;
import org.apache.beam.sdk.transforms.ParDo;
import org.apache.beam.sdk.values.KV;
import org.apache.beam.sdk.values.PCollection;
import org.joda.time.DateTime;

import com.google.bigtable.admin.v2.ColumnFamily;
import com.google.bigtable.admin.v2.CreateTableRequest;
import com.google.bigtable.admin.v2.GetTableRequest;
import com.google.bigtable.admin.v2.Table;
import com.google.bigtable.v2.Mutation;
import com.google.cloud.bigtable.config.BigtableOptions;
import com.google.cloud.bigtable.config.CredentialOptions;
import com.google.cloud.bigtable.grpc.BigtableSession;
import com.google.cloud.bigtable.grpc.BigtableTableAdminClient;
import com.google.cloud.training.flights.AddRealtimePrediction.MyOptions;
import com.google.cloud.training.flights.Flight.INPUTCOLS;
import com.google.protobuf.ByteString;

@SuppressWarnings("serial")
public class PubSubBigtable extends PubSubInput {
  private static String INSTANCE_ID = "flights";
  private String getInstanceName(MyOptions options) {
    return String.format("projects/%s/instances/%s", options.getProject(), INSTANCE_ID);
  }
  private static String TABLE_ID = "predictions";
  private String getTableName(MyOptions options) {
    return String.format("%s/tables/%s", getInstanceName(options), TABLE_ID);
  }
  private static final String CF_FAMILY = "FL";
  
  @Override
  public void writeFlights(PCollection<Flight> outFlights, MyOptions options) {
    PCollection<FlightPred> preds = addPredictionInBatches(outFlights);
    BigtableOptions.Builder optionsBuilder = //
        new BigtableOptions.Builder()//
            .setProjectId(options.getProject()) //
            .setInstanceId(INSTANCE_ID).setUserAgent("datascience-on-gcp");
    createEmptyTable(options, optionsBuilder);
    PCollection<KV<ByteString, Iterable<Mutation>>> mutations = toMutations(preds);
    mutations.apply("write:cbt", //
        BigtableIO.write().withBigtableOptions(optionsBuilder.build()).withTableId(TABLE_ID));
  }

  private PCollection<KV<ByteString, Iterable<Mutation>>> toMutations(PCollection<FlightPred> preds) {
    return preds.apply("pred->mutation", ParDo.of(new DoFn<FlightPred, KV<ByteString, Iterable<Mutation>>>() {
      @ProcessElement
      public void processElement(ProcessContext c) throws Exception {
        FlightPred pred = c.element();
        String key = pred.flight.getField(INPUTCOLS.ORIGIN) //
            + "#" + pred.flight.getField(INPUTCOLS.DEST) // 
            + "#" + pred.flight.getField(INPUTCOLS.CARRIER) //
            + "#" + getReverseTimestamp(pred.flight.getFieldAsDateTime(INPUTCOLS.CRS_DEP_TIME));
        List<Mutation> mutations = new ArrayList<>();
        long ts = pred.flight.getEventTimestamp().getMillis();
        for (INPUTCOLS col : INPUTCOLS.values()) {
          addCell(mutations, col.name(), pred.flight.getField(col), ts);
        }
        if (pred.ontime >= 0) {
          addCell(mutations, "ontime", new DecimalFormat("0.00").format(pred.ontime), ts);
        }
        c.output(KV.of(ByteString.copyFromUtf8(key), mutations));
      }

      private long getReverseTimestamp(DateTime timestamp) {
        return Long.MAX_VALUE - timestamp.getMillis();
      }
    }));
  }

  private void addCell(List<Mutation> mutations, String cellName, String cellValue, long ts) {
    if (cellValue.length() > 0) {
      ByteString value = ByteString.copyFromUtf8(cellValue);
      ByteString colname = ByteString.copyFromUtf8(cellName);
      Mutation m = //
          Mutation.newBuilder().setSetCell(//
                  Mutation.SetCell.newBuilder() //
                      .setValue(value)//
                      .setFamilyName(CF_FAMILY)//
                      .setColumnQualifier(colname)//
                      .setTimestampMicros(ts) //
          ).build();
      mutations.add(m);
    }
  }

  private void createEmptyTable(MyOptions options, BigtableOptions.Builder optionsBuilder) {
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
}
