package com.google.cloud.training.mlongcp;

import java.text.DecimalFormat;

import org.apache.beam.sdk.Pipeline;
import org.apache.beam.sdk.io.TextIO;
import org.apache.beam.sdk.transforms.DoFn;
import org.apache.beam.sdk.transforms.ParDo;
import org.apache.beam.sdk.values.PCollection;

import com.google.cloud.training.mlongcp.AddPrediction.MyOptions;

@SuppressWarnings("serial")
public class TextInputOutput extends InputOutput {
  @Override
  public PCollection<Baby> readInstances(Pipeline p, MyOptions options) {
    String inputFile = options.getInput();
    LOG.info("Reading data from " + inputFile);

    PCollection<Baby> babies = p //
        .apply("ReadLines", TextIO.read().from(inputFile)) //
        .apply("Parse", ParDo.of(new DoFn<String, Baby>() {
          @ProcessElement
          public void processElement(ProcessContext c) throws Exception {
            String line = c.element();
            Baby f = Baby.fromCsv(line);
            if (f != null) {
              c.output(f);
            }
          }
        }));
    return babies;
  }

  @Override
  public void writePredictions(PCollection<Baby> instances, MyOptions options) {
    try {
      PCollection<BabyPred> prds = addPredictionInBatches(instances);
      PCollection<String> lines = predToCsv(prds);
      lines.apply("Write", TextIO.write().to(options.getOutput() + "flightPreds").withSuffix(".csv"));
    } catch (Throwable t) {
      LOG.warn("Inference failed", t);
    }
  }

  private PCollection<String> predToCsv(PCollection<BabyPred> preds) {
    return preds.apply("pred->csv", ParDo.of(new DoFn<BabyPred, String>() {
      @ProcessElement
      public void processElement(ProcessContext c) throws Exception {
        BabyPred pred = c.element();
        String csv = String.join(",", pred.flight.getFields());
        if (pred.predictedWeight >= 0) {
          csv = csv + "," + new DecimalFormat("0.00").format(pred.predictedWeight);
        } else {
          csv = csv + ","; // empty string -> null
        }
        c.output(csv);
      }})) //
;
  }
}
