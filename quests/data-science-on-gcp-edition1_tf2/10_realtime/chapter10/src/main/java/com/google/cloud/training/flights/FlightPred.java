package com.google.cloud.training.flights;

import org.apache.beam.sdk.coders.AvroCoder;
import org.apache.beam.sdk.coders.DefaultCoder;

@DefaultCoder(AvroCoder.class)
public class FlightPred {
  Flight flight;
  double ontime;
  
  FlightPred(){}
  FlightPred(Flight f, double ontime) {
    this.flight = f;
    this.ontime = ontime;
  }
}
