package com.google.cloud.training.mlongcp;

import java.util.ArrayList;
import java.util.List;

import org.apache.beam.sdk.Pipeline;
import org.apache.beam.sdk.io.gcp.bigquery.BigQueryIO;
import org.apache.beam.sdk.io.gcp.pubsub.PubsubIO;
import org.apache.beam.sdk.transforms.DoFn;
import org.apache.beam.sdk.transforms.ParDo;
import org.apache.beam.sdk.values.PCollection;

import com.google.api.services.bigquery.model.TableFieldSchema;
import com.google.api.services.bigquery.model.TableRow;
import com.google.api.services.bigquery.model.TableSchema;
import com.google.cloud.training.mlongcp.AddPrediction.MyOptions;
import com.google.cloud.training.mlongcp.Baby.INPUTCOLS;

@SuppressWarnings("serial")
public class PubSubBigQuery extends InputOutput {

  @Override
  public PCollection<Baby> readInstances(Pipeline p, MyOptions options) {
    String topic = "projects/" + options.getProject() + "/topics/" + options.getInput();
    LOG.info("Reading from pub/sub topic " + topic);

    return p.apply("combined:read",
        PubsubIO.readStrings().fromTopic(topic).withTimestampAttribute("EventTimeStamp")) //
        .apply("parse", ParDo.of(new DoFn<String, Baby>() {
          @ProcessElement
          public void processElement(ProcessContext c) throws Exception {
            String message = c.element();
            String[] lines = message.split("\n");
            for (String line : lines) {
              Baby f = Baby.fromCsv(line);
              if (f != null) {
                c.output(f);
              }
            }
          }
        }));
  } 
  
  @Override
  public void writePredictions(PCollection<Baby> instances, MyOptions options) {
    String outputTable = options.getProject() + ':' + options.getOutput();
    LOG.info("Writing to BigQuery table " + outputTable);    
    
    TableSchema schema = new TableSchema().setFields(getTableFields());
    PCollection<BabyPred> preds = addPredictionInBatches(instances);
    PCollection<TableRow> rows = toTableRows(preds);
    rows.apply("write_toBQ",BigQueryIO.writeTableRows().to(outputTable) //
        .withSchema(schema)//
        .withWriteDisposition(BigQueryIO.Write.WriteDisposition.WRITE_APPEND)
        .withCreateDisposition(BigQueryIO.Write.CreateDisposition.CREATE_IF_NEEDED));
  }

  private PCollection<TableRow> toTableRows(PCollection<BabyPred> preds) {
    return preds.apply("pred->row", ParDo.of(new DoFn<BabyPred, TableRow>() {
      @ProcessElement
      public void processElement(ProcessContext c) throws Exception {
        BabyPred pred = c.element();
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
        if (pred.predictedWeight >= 0) {
          row.set("predicted_weight_pounds", Math.round(pred.predictedWeight*100)/100.0);
        }
        c.output(row);
      }})) //
        ;
  }

  private String[] types;
  public PubSubBigQuery() {
    this.types = new String[INPUTCOLS.values().length];
    for (int i=0; i < types.length; ++i) {
      types[i] = "STRING";
    }
    types[INPUTCOLS.weight_pounds.ordinal()] = "FLOAT";
    types[INPUTCOLS.mother_age.ordinal()] = "FLOAT";
    types[INPUTCOLS.plurality.ordinal()] = "FLOAT";
    types[INPUTCOLS.gestation_weeks.ordinal()] = "FLOAT";
  }

  private List<TableFieldSchema> getTableFields() {
    List<TableFieldSchema> fields = new ArrayList<>();
    for (int i=0; i < types.length; ++i) {
      String name = INPUTCOLS.values()[i].name();
      fields.add(new TableFieldSchema().setName(name).setType(types[i]));
    }
    fields.add(new TableFieldSchema().setName("predicted_weight_pounds").setType("FLOAT"));
    return fields;
  }    
}
