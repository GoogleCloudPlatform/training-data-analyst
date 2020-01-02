package com.mypackage.pipeline;

import com.google.common.annotations.VisibleForTesting;
import org.apache.beam.sdk.coders.DefaultCoder;
import org.apache.beam.sdk.coders.SerializableCoder;

import java.io.Serializable;

@VisibleForTesting
/**
 * A class used for parsing JSON web server events
 */
@DefaultCoder(SerializableCoder.class)
public class CommonLog implements Serializable {
    public String user_id;
    public String ip;
    public double lat;
    public double lng;
    public String timestamp;
    public String http_request;
    public String user_agent;
    public int http_response;
    public int num_bytes;
}