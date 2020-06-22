package com.mypackage.pipeline;

import com.google.common.annotations.VisibleForTesting;
import org.apache.beam.sdk.coders.DefaultCoder;
import org.apache.beam.sdk.coders.SerializableCoder;
import org.apache.beam.sdk.schemas.JavaFieldSchema;
import org.apache.beam.sdk.schemas.annotations.DefaultSchema;

import java.io.Serializable;

@VisibleForTesting
/**
 * A class used for parsing JSON web server events
 */
@DefaultSchema(JavaFieldSchema.class)
public class CommonLog {
    public String user_id;
    public String ip;
    public double lat;
    public double lng;
    public String timestamp;
    public String http_request;
    @javax.annotation.Nullable
    public String user_agent;
    public int http_response;
    public int num_bytes;
}