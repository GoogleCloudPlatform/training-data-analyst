package com.google.cloud.training.mlongcp;

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
import com.google.cloud.training.mlongcp.Baby.INPUTCOLS;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

public class BabyweightMLService {
  private static final Logger LOG = LoggerFactory.getLogger(BabyweightMLService.class);
  private static final String PROJECT = "cloud-training-demos";
  private static String       MODEL   = "babyweight";
  private static String       VERSION = "ml_on_gcp";

  static class Instance {
    String is_male, plurality;
    float mother_age, gestation_weeks; 
    
    Instance() {}
    Instance(Baby f) {
      this.is_male = f.getField(Baby.INPUTCOLS.is_male);
      this.mother_age = f.getFieldAsFloat(Baby.INPUTCOLS.mother_age);
      this.plurality = f.getField(Baby.INPUTCOLS.plurality);
      this.gestation_weeks = f.getFieldAsFloat(Baby.INPUTCOLS.gestation_weeks);
    }
  }

  static class Request {
    List<Instance> instances = new ArrayList<>();
  }

  static class Prediction {
    List<Double> predictions;
  }

  static class Response {
    List<Prediction> predictions = new ArrayList<>();

    public double[] getPredictedBabyWeights() {
      double[] result = new double[predictions.size()];
      for (int i=0; i < result.length; ++i) {
        Prediction pred = predictions.get(i);
        result[i] = pred.predictions.get(0);
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
  
  public static double[] mock_batchPredict(Iterable<Baby> instances) throws IOException, GeneralSecurityException {
    int n = 0;
    for (@SuppressWarnings("unused") Baby f : instances) {
      ++n;
    }
    LOG.info("Mock prediction for " + n + " instances");
    double[] result = new double[n];
    for (int i=0; i < n; ++i) {
      result[i] = Math.random() * 10;
    }
    return result;
  }
  
  public static double[] batchPredict(Iterable<Baby> instances) throws IOException, GeneralSecurityException {
    Request request = new Request();
    for (Baby f : instances) {
      request.instances.add(new Instance(f));
    }
    Response resp = sendRequest(request);
    double[] result = resp.getPredictedBabyWeights();
    return result;
  }

  public static double predict(Baby f, double defaultValue) throws IOException, GeneralSecurityException {
    
      Request request = new Request();

      // fill in actual values
      Instance instance = new Instance(f);
      request.instances.add(instance);

      // send request
      Response resp = sendRequest(request);
      double[] result = resp.getPredictedBabyWeights();
      if (result.length > 0) {
        return result[0];
      } else {
        return defaultValue;
      }
    
  }

  public static void main(String[] args) throws Exception {   
    // create request
    Request request = new Request();

    Instance instance = new Instance();
    instance.is_male = "True";
    instance.mother_age = 26;
    instance.plurality = "Twins(2)";
    instance.gestation_weeks = 37;

    request.instances.add(instance);

    // send request to service
    Response resp = sendRequest(request);
    System.out.println(resp.getPredictedBabyWeights()[0]);

    Baby f = Baby.fromCsv("5.4233716452,True,13,Single(1),37.0,124458947937444850");
    System.out.println("predicted=" + predict(f, -1) + " actual=" + f.getFieldAsFloat(INPUTCOLS.weight_pounds));
  }

}
