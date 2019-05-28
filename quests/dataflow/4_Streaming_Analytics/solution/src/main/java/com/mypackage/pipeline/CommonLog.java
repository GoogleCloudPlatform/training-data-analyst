package com.mypackage.pipeline;

import com.google.common.annotations.VisibleForTesting;
import com.google.gson.annotations.Expose;
import org.apache.beam.sdk.coders.DefaultCoder;
import org.apache.beam.sdk.coders.SerializableCoder;

import java.io.Serializable;

@VisibleForTesting
/**
 * A class used for parsing JSON web server events
 */
@DefaultCoder(SerializableCoder.class)
public class CommonLog implements Serializable {
    @Expose()
    public String user_id;
    @Expose()
    public String ip;
    @Expose()
    public double lat;
    @Expose()
    public double lng;
    @Expose()
    public String event_timestamp;
    @Expose()
    public String http_request;
    @Expose()
    public String user_agent;
    @Expose()
    public int http_response;
    @Expose()
    public int num_bytes;
    // This field added to simplify code for this lab
    public String processing_timestamp;


    public void setProcessing_timestamp(String processing_timestamp) {
        this.processing_timestamp = processing_timestamp;
    }

}