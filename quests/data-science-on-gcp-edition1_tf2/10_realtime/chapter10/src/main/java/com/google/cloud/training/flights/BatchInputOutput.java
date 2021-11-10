package com.google.cloud.training.flights;

import java.text.DecimalFormat;

import org.apache.beam.sdk.Pipeline;
import org.apache.beam.sdk.io.TextIO;
import org.apache.beam.sdk.io.gcp.bigquery.BigQueryIO;
import org.apache.beam.sdk.transforms.DoFn;
import org.apache.beam.sdk.transforms.ParDo;
import org.apache.beam.sdk.values.PCollection;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.google.api.services.bigquery.model.TableRow;
import com.google.cloud.training.flights.AddRealtimePrediction.MyOptions;

@SuppressWarnings("serial")
public class BatchInputOutput extends InputOutput {
  private static final Logger LOG = LoggerFactory.getLogger(InputOutput.class);
  
  private static String getOutput(MyOptions opts) {
    return "gs://BUCKET/flights/chapter10/output/".replace("BUCKET", opts.getBucket());
  }
  
  @Override
  public PCollection<Flight> readFlights(Pipeline p, MyOptions options) {
    String query = "SELECT EVENT_DATA FROM flights.simevents WHERE ";
    query += " STRING(FL_DATE) = '2015-01-04' AND ";
    query += " (EVENT = 'wheelsoff' OR EVENT = 'arrived') ";
    LOG.info(query);

    PCollection<Flight> allFlights = p //
        .apply("ReadLines", BigQueryIO.read().fromQuery(query)) //
        .apply("ParseFlights", ParDo.of(new DoFn<TableRow, Flight>() {
          @ProcessElement
          public void processElement(ProcessContext c) throws Exception {
            TableRow row = c.element();
            String line = (String) row.getOrDefault("EVENT_DATA", "");
            Flight f = Flight.fromCsv(line);
            if (f != null) {
              c.outputWithTimestamp(f, f.getEventTimestamp());
            }
          }
        }));
    return allFlights;
  }

  @Override
  public void writeFlights(PCollection<Flight> outFlights, MyOptions options) {
    // PCollection<String> lines = addPredictionOneByOne(outFlights);
    try {
      PCollection<FlightPred> prds = addPredictionInBatches(outFlights);
      PCollection<String> lines = predToCsv(prds);
      lines.apply("Write", TextIO.write().to(getOutput(options) + "flightPreds").withSuffix(".csv"));
    } catch (Throwable t) {
      LOG.warn("Inference failed", t);
    }
  }

  private PCollection<String> predToCsv(PCollection<FlightPred> preds) {
    return preds.apply("pred->csv", ParDo.of(new DoFn<FlightPred, String>() {
      @ProcessElement
      public void processElement(ProcessContext c) throws Exception {
        FlightPred pred = c.element();
        String csv = String.join(",", pred.flight.getFields());
        if (pred.ontime >= 0) {
          csv = csv + "," + new DecimalFormat("0.00").format(pred.ontime);
        } else {
          csv = csv + ","; // empty string -> null
        }
        c.output(csv);
      }})) //
;
  }
}
