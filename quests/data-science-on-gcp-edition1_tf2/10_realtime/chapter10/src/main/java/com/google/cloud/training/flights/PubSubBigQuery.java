package com.google.cloud.training.flights;

import java.util.ArrayList;
import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import org.apache.beam.sdk.io.gcp.bigquery.BigQueryIO;
import org.apache.beam.sdk.transforms.DoFn;
import org.apache.beam.sdk.transforms.ParDo;
import org.apache.beam.sdk.values.PCollection;

import com.google.api.services.bigquery.model.TableFieldSchema;
import com.google.api.services.bigquery.model.TableRow;
import com.google.api.services.bigquery.model.TableSchema;
import com.google.cloud.training.flights.AddRealtimePrediction.MyOptions;
import com.google.cloud.training.flights.Flight.INPUTCOLS;

@SuppressWarnings("serial")
public class PubSubBigQuery extends PubSubInput {
  private static final String BQ_TABLE_NAME = "flights.predictions";
  private static final Logger LOG = LoggerFactory.getLogger(FlightsMLService.class);

  //    private SerializableFunction<ValueInSingleWindow, String> getTableNameFunction() {
  //      return new SerializableFunction<ValueInSingleWindow, String>() {
  //                  public String apply(ValueInSingleWindow value) {
  //                     // The cast below is safe because CalendarWindows.days(1) produces IntervalWindows.
  //                     String dayString = DateTimeFormat.forPattern("yyyy_MM_dd")
  //                          .withZone(DateTimeZone.UTC)
  //                          .print(((IntervalWindow) value.getWindow()).start());
  //                     return BQ_TABLE_NAME + "_" + dayString;
  //                   }
  //      }
  //    }

  @Override
  public void writeFlights(PCollection<Flight> outFlights, MyOptions options) {
    String outputTable = options.getProject() + ':' + BQ_TABLE_NAME;
    TableSchema schema = new TableSchema().setFields(getTableFields());
    PCollection<FlightPred> preds = addPredictionInBatches(outFlights);
    PCollection<TableRow> rows = toTableRows(preds);
    rows.apply("flights:write_toBQ",BigQueryIO.writeTableRows().to(outputTable) //
        .withSchema(schema)//
        .withWriteDisposition(BigQueryIO.Write.WriteDisposition.WRITE_APPEND)
        .withCreateDisposition(BigQueryIO.Write.CreateDisposition.CREATE_IF_NEEDED));
  }

  private PCollection<TableRow> toTableRows(PCollection<FlightPred> preds) {
    return preds.apply("pred->row", ParDo.of(new DoFn<FlightPred, TableRow>() {
      @ProcessElement
      public void processElement(ProcessContext c) throws Exception {
        FlightPred pred = c.element();
        TableRow row = new TableRow();
        for (int i=0; i < types.length; ++i) {
          INPUTCOLS col = INPUTCOLS.values()[i];
          String name = col.name();
          String value = pred.flight.getField(col);

          if (value.length() > 0) {
            if (types[i].equals("FLOAT")) {
              row.set(name, Float.parseFloat(value));
            } else {
              row.set(name, value);
            }
          }
        }
        if (pred.ontime >= 0) {
          row.set("ontime", Math.round(pred.ontime*100)/100.0);
        }
        c.output(row);
      }})) //
        ;
  }

  private String[] types;
  public PubSubBigQuery() {
    this.types = new String[INPUTCOLS.values().length];   
    // Column data types are set by pattern - 
    String[] floatPatterns = new String[] {"AIRPORT_LAT", "AIRPORT_LON", "DELAY", "DISTANCE", "TAXI"};
    String[] timePatterns  = new String[] {"TIME", "WHEELS" };
    for (int i=0; i < types.length; ++i) {
      String name = INPUTCOLS.values()[i].name();
      types[i] = "STRING";
      for (String pattern : floatPatterns) {
        if (name.contains(pattern)) {
          types[i] = "FLOAT";
        }
      }
      for (String pattern : timePatterns) {
        if (name.contains(pattern)) {
          types[i] = "TIMESTAMP";
        }
      }
    }
  }

  private List<TableFieldSchema> getTableFields() {
    List<TableFieldSchema> fields = new ArrayList<>();
    for (int i=0; i < types.length; ++i) {
      String name = INPUTCOLS.values()[i].name();
      fields.add(new TableFieldSchema().setName(name).setType(types[i]));
    }
    fields.add(new TableFieldSchema().setName("ontime").setType("FLOAT"));
    return fields;
  }    
}
