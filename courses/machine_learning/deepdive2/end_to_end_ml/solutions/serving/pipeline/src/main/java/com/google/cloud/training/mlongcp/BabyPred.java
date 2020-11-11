package com.google.cloud.training.mlongcp;

import org.apache.beam.sdk.coders.AvroCoder;
import org.apache.beam.sdk.coders.DefaultCoder;

@DefaultCoder(AvroCoder.class)
public class BabyPred {
  Baby flight;
  double predictedWeight;
  
  BabyPred(){}
  BabyPred(Baby f, double pred) {
    this.flight = f;
    this.predictedWeight = pred;
  }
}
