package com.google.cloud.training.flights;

import java.io.IOException;
import java.security.GeneralSecurityException;
import java.util.ArrayList;
import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.google.api.client.googleapis.auth.oauth2.GoogleCredential;
import com.google.api.client.googleapis.javanet.GoogleNetHttpTransport;
import com.google.api.client.http.ByteArrayContent;
import com.google.api.client.http.GenericUrl;
import com.google.api.client.http.HttpBackOffUnsuccessfulResponseHandler;
import com.google.api.client.http.HttpContent;
import com.google.api.client.http.HttpRequest;
import com.google.api.client.http.HttpRequestFactory;
import com.google.api.client.http.HttpTransport;
import com.google.api.client.util.ExponentialBackOff;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

public class FlightsMLService {
  private static final Logger LOG = LoggerFactory.getLogger(FlightsMLService.class);
  private static final String PROJECT = "cloud-training-demos";
  private static String       MODEL   = "flights";
  private static String       VERSION = "tf2";

  static class Instance {
    double dep_delay, taxiout, distance, avg_dep_delay, avg_arr_delay, dep_lat, dep_lon, arr_lat, arr_lon;
    String carrier, origin, dest;

    Instance() {}
    Instance(Flight f) {
      this.dep_delay = f.getFieldAsFloat(Flight.INPUTCOLS.DEP_DELAY);
      this.taxiout = f.getFieldAsFloat(Flight.INPUTCOLS.TAXI_OUT);
      this.distance = f.getFieldAsFloat(Flight.INPUTCOLS.DISTANCE);
      this.avg_dep_delay = f.avgDepartureDelay;
      this.avg_arr_delay = f.avgDepartureDelay;
      this.carrier = f.getField(Flight.INPUTCOLS.UNIQUE_CARRIER);
      this.dep_lat = f.getFieldAsFloat(Flight.INPUTCOLS.DEP_AIRPORT_LAT);
      this.dep_lon = f.getFieldAsFloat(Flight.INPUTCOLS.DEP_AIRPORT_LON);
      this.arr_lat = f.getFieldAsFloat(Flight.INPUTCOLS.ARR_AIRPORT_LAT);
      this.arr_lon = f.getFieldAsFloat(Flight.INPUTCOLS.ARR_AIRPORT_LON);
      this.origin = f.getField(Flight.INPUTCOLS.ORIGIN);
      this.dest = f.getField(Flight.INPUTCOLS.DEST);
    }
  }

  static class Request {
    List<Instance> instances = new ArrayList<>();
  }

  // Update for changes in Cloud AI platform default prediction response
  static class Prediction {
    List<Double> pred = new ArrayList<>();
  }

  static class Response {
    List<Prediction> predictions = new ArrayList<>();

    public double[] getOntimeProbability(double defaultValue) {
      double[] result = new double[predictions.size()];
      for (int i=0; i < result.length; ++i) {
        Prediction pred = predictions.get(i);
        if (pred.pred.size() > 0) {
          result[i] = pred.pred.get(0);
        } else {
          result[i] = defaultValue;
        }
      }
      return result;
    }
  }

  static Response sendRequest(Request req) throws IOException, GeneralSecurityException {
    long startTime = System.currentTimeMillis();
    try {
      // create JSON of request
      Gson gson = new GsonBuilder().create();
      String json = gson.toJson(req, Request.class);
      LOG.debug(json);

      // our service's URL
      String endpoint = "https://ml.googleapis.com/v1/projects/" 
          + String.format("%s/models/%s/versions/%s:predict", PROJECT, MODEL, VERSION);
      GenericUrl url = new GenericUrl(endpoint);

      // set up https
      GoogleCredential credential = GoogleCredential.getApplicationDefault();
      HttpTransport httpTransport = GoogleNetHttpTransport.newTrustedTransport();
      HttpRequestFactory requestFactory = httpTransport.createRequestFactory(credential);
      HttpContent content = new ByteArrayContent("application/json", json.getBytes());
      
      // send request
      HttpRequest request = requestFactory.buildRequest("POST", url, content);
      request.setUnsuccessfulResponseHandler(new HttpBackOffUnsuccessfulResponseHandler(new ExponentialBackOff()));
      request.setReadTimeout(5 * 60 * 1000); // 5 minutes
      String response = request.execute().parseAsString();
      LOG.debug(response);
      
      // parse response
      return gson.fromJson(response, Response.class);
    }
    finally {
      long endTime = System.currentTimeMillis();
      LOG.debug((endTime - startTime) + " msecs overall");
    }
  }
  
  public static double[] mock_batchPredict(Iterable<Flight> flights, float defaultValue) throws IOException, GeneralSecurityException {
    int n = 0;
    for (@SuppressWarnings("unused") Flight f : flights) {
      ++n;
    }
    double[] result = new double[n];
    for (int i=0; i < n; ++i) {
      result[i] = defaultValue;
    }
    return result;
  }
  
  public static double[] batchPredict(Iterable<Flight> flights, float defaultValue) throws IOException, GeneralSecurityException {
    Request request = new Request();
    for (Flight f : flights) {
      request.instances.add(new Instance(f));
    }
    Response resp = sendRequest(request);
    double[] result = resp.getOntimeProbability(defaultValue);
    return result;
  }

  public static double predictOntimeProbability(Flight f, double defaultValue) throws IOException, GeneralSecurityException {
    if (f.isNotCancelled() && f.isNotDiverted()) {
      Request request = new Request();

      // fill in actual values
      Instance instance = new Instance(f);
      request.instances.add(instance);

      // send request
      Response resp = sendRequest(request);
      double[] result = resp.getOntimeProbability(defaultValue);
      if (result.length > 0) {
        return result[0];
      } else {
        return defaultValue;
      }
    }
    return defaultValue;
  }

  public static void main(String[] args) throws Exception {
    // create request
    Request request = new Request();

    Instance instance = new Instance();
    instance.dep_delay = 16;
    instance.taxiout = 13;
    instance.distance = 160;
    instance.avg_dep_delay = 13.34;
    instance.avg_arr_delay = 67;
    instance.carrier = "AS";
    instance.dep_lat = 61.17;
    instance.dep_lon = -150;
    instance.arr_lat = 60.49;
    instance.arr_lon = -145.48;
    instance.origin = "ANC";
    instance.dest = "CDV";

    request.instances.add(instance);

    // send request to service
    Response resp = sendRequest(request);
    System.out.println(resp.getOntimeProbability(-1)[0]);

    Flight f = Flight.fromCsv("2015-01-04,EV,20366,EV,2563,11298,1129803,30194,DFW,11140,1114004,31140,CRP,2015-01-04T13:25:00,2015-01-04T13:33:00,8.00,16.00,2015-01-04T13:49:00,,,2015-01-04T14:45:00,,,0.00,,,354.00,32.89694444,-97.03805556,-21600.0,27.77083333,-97.50111111,-21600.0,wheelsoff,2015-01-04T13:49:00");
    f.avgArrivalDelay = 13;
    f.avgDepartureDelay = 12;
    System.out.println("flight: " + predictOntimeProbability(f, -1));
  }

}
