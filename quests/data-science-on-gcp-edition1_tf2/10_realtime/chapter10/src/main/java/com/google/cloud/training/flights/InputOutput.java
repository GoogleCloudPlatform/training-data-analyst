package com.google.cloud.training.flights;

import java.io.Serializable;

import org.apache.beam.sdk.Pipeline;
import org.apache.beam.sdk.transforms.DoFn;
import org.apache.beam.sdk.transforms.GroupByKey;
import org.apache.beam.sdk.transforms.ParDo;
import org.apache.beam.sdk.values.KV;
import org.apache.beam.sdk.values.PCollection;

import com.google.cloud.training.flights.AddRealtimePrediction.MyOptions;
import com.google.cloud.training.flights.Flight.INPUTCOLS;

@SuppressWarnings("serial")
public abstract class InputOutput implements Serializable {
  public abstract PCollection<Flight> readFlights(Pipeline p, MyOptions options);
  public abstract void writeFlights(PCollection<Flight> outFlights, MyOptions options);

  private static class CreateBatch extends DoFn<Flight, KV<String, Flight>> {
    private static final int NUM_BATCHES = 2;
    @ProcessElement
    public void processElement(ProcessContext c) throws Exception {
      Flight f = c.element();
      String key;
      if (f.isNotCancelled() && f.isNotDiverted()) {
        key = f.getField(INPUTCOLS.EVENT); // "arrived" "wheelsoff"
      } else {
        key = "ignored";
      }
      // add a randomized part to provide batching capability
      key = key + " " + (System.identityHashCode(f) % NUM_BATCHES);
      c.output(KV.of(key, f));
    }
  }
  
  public static PCollection<FlightPred> addPredictionInBatches(PCollection<Flight> outFlights) {
    return addPredictionInBatches(outFlights, false);
  }
  
  public static PCollection<FlightPred> addPredictionInBatches(PCollection<Flight> outFlights, //
      boolean predictArrivedAlso) {
    return outFlights //
        .apply("Batch->Flight", ParDo.of(new CreateBatch())) //
        .apply("CreateBatches", GroupByKey.<String, Flight> create()) // within window
        .apply("Inference", ParDo.of(new DoFn<KV<String, Iterable<Flight>>, FlightPred>() {
          @ProcessElement
          public void processElement(ProcessContext c) throws Exception {
            String key = c.element().getKey();
            Iterable<Flight> flights = c.element().getValue();
             
            // write out all the ignored events as-is
            if (key.startsWith("ignored")) {
              for (Flight f : flights) {
                c.output(new FlightPred(f, -1));
              }
              return;
            }

            // for arrived events, emit actual ontime performance
            if (key.startsWith("arrived") && !predictArrivedAlso) {
              for (Flight f : flights) {
                double ontime = f.getFieldAsFloat(INPUTCOLS.ARR_DELAY, 0) < 15 ? 1 : 0;
                c.output(new FlightPred(f, ontime));
              }
              return;
            }

            // do ml inference for wheelsoff events, but as batch
            double[] result = FlightsMLService.batchPredict(flights, -5);
            int resultno = 0;
            for (Flight f : flights) {
              double ontime = result[resultno++];
              c.output(new FlightPred(f, ontime));
            }
          }
        }));
  }
  


  @SuppressWarnings("unused")
  private static PCollection<FlightPred> addPredictionOneByOne(PCollection<Flight> outFlights) {
    return outFlights //
        .apply("Inference", ParDo.of(new DoFn<Flight, FlightPred>() {
          @ProcessElement
          public void processElement(ProcessContext c) throws Exception {
            Flight f = c.element();
            double ontime = -5;
            if (f.isNotCancelled() && f.isNotDiverted()) {
              if (f.getField(INPUTCOLS.EVENT).equals("arrived")) {
                // actual ontime performance
                ontime = f.getFieldAsFloat(INPUTCOLS.ARR_DELAY, 0) < 15 ? 1 : 0;
              } else {
                // wheelsoff: predict ontime arrival probability
                ontime = FlightsMLService.predictOntimeProbability(f, -5.0);
              }
            }
            c.output(new FlightPred(f, ontime));
          }
        }));
  }
}
