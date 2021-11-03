/*
 * Copyright (C) 2016 Google Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not
 * use this file except in compliance with the License. You may obtain a copy of
 * the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations under
 * the License.
 */

package com.google.cloud.training.flights;

import java.util.Arrays;

import org.apache.beam.sdk.coders.AvroCoder;
import org.apache.beam.sdk.coders.DefaultCoder;
import org.joda.time.DateTime;
import org.joda.time.Instant;
import org.joda.time.format.DateTimeFormat;
import org.joda.time.format.DateTimeFormatter;

/**
 * @author vlakshmanan
 *
 */
@DefaultCoder(AvroCoder.class)
public class Flight {
  public enum INPUTCOLS {
    FL_DATE, UNIQUE_CARRIER, AIRLINE_ID, CARRIER, FL_NUM, ORIGIN_AIRPORT_ID, ORIGIN_AIRPORT_SEQ_ID, ORIGIN_CITY_MARKET_ID, ORIGIN, DEST_AIRPORT_ID, DEST_AIRPORT_SEQ_ID, DEST_CITY_MARKET_ID, DEST, CRS_DEP_TIME, DEP_TIME, DEP_DELAY, TAXI_OUT, WHEELS_OFF, WHEELS_ON, TAXI_IN, CRS_ARR_TIME, ARR_TIME, ARR_DELAY, CANCELLED, CANCELLATION_CODE, DIVERTED, DISTANCE, DEP_AIRPORT_LAT, DEP_AIRPORT_LON, DEP_AIRPORT_TZOFFSET, ARR_AIRPORT_LAT, ARR_AIRPORT_LON, ARR_AIRPORT_TZOFFSET, EVENT, NOTIFY_TIME;
  }

  private String[] fields;
  float            avgDepartureDelay, avgArrivalDelay;

  public static Flight fromCsv(String line) {
    Flight f = new Flight();
    f.fields = line.split(",");
    f.avgArrivalDelay = f.avgDepartureDelay = Float.NaN;
    if (f.fields.length == INPUTCOLS.values().length) {
      return f;
    }
    return null; // malformed
  }
  
  public String[] getFields() {
    return fields;
  }

  public boolean isNotDiverted() {
    String col = getField(INPUTCOLS.DIVERTED);
    return col.length() == 0 || col.equals("0.00");
  }

  public boolean isNotCancelled() {
    String col = getField(INPUTCOLS.CANCELLED);
    return col.length() == 0 || col.equals("0.00");
  }

  public String getField(INPUTCOLS col) {
    return fields[col.ordinal()];
  }

  public float getFieldAsFloat(INPUTCOLS col) {
    return Float.parseFloat(fields[col.ordinal()]);
  }
  
  public DateTime getFieldAsDateTime(INPUTCOLS col) {
    String timestamp = getField(col).replace('T', ' ');
    return fmt.parseDateTime(timestamp);   
  }

  public float getFieldAsFloat(INPUTCOLS col, float defaultValue) {
    String s = fields[col.ordinal()];
    if (s.length() > 0) {
      return Float.parseFloat(s);
    } else {
      return defaultValue;
    }
  }
  
  private static DateTimeFormatter fmt = DateTimeFormat.forPattern("yyyy-MM-dd HH:mm:ss");

  public int getDepartureHour() {
    float offset = getFieldAsFloat(INPUTCOLS.DEP_AIRPORT_TZOFFSET);
    DateTime dt = getFieldAsDateTime(INPUTCOLS.DEP_TIME);
    dt = dt.plusMinutes((int) (0.5 + offset));
    return dt.getHourOfDay();
  }

  private float[] getFloatFeatures() {
    float[] result = new float[5];
    int col = 0;
    result[col++] = Float.parseFloat(fields[INPUTCOLS.DEP_DELAY.ordinal()]);
    result[col++] = Float.parseFloat(fields[INPUTCOLS.TAXI_OUT.ordinal()]);
    result[col++] = Float.parseFloat(fields[INPUTCOLS.DISTANCE.ordinal()]);
    result[col++] = avgDepartureDelay;
    result[col++] = avgArrivalDelay;
    return result;
  }

  public String toTrainingCsv() {
    float[] floatFeatures = this.getFloatFeatures();
    float arrivalDelay = Float.parseFloat(fields[INPUTCOLS.ARR_DELAY.ordinal()]);
    boolean ontime = arrivalDelay < 15;
    StringBuilder sb = new StringBuilder();
    sb.append(ontime ? 1.0 : 0.0);
    sb.append(",");
    for (int i = 0; i < floatFeatures.length; ++i) {
      sb.append(floatFeatures[i]);
      sb.append(",");
    }
    INPUTCOLS[] stringFeatures = {INPUTCOLS.UNIQUE_CARRIER, INPUTCOLS.DEP_AIRPORT_LAT, INPUTCOLS.DEP_AIRPORT_LON, INPUTCOLS.ARR_AIRPORT_LAT, INPUTCOLS.ARR_AIRPORT_LON, INPUTCOLS.ORIGIN, INPUTCOLS.DEST};
    for (INPUTCOLS col : stringFeatures) {
      sb.append(fields[col.ordinal()]);
      sb.append(",");
    }
    sb.deleteCharAt(sb.length() - 1); // last comma
    return sb.toString();
  }

  public Flight newCopy() {
    Flight f = new Flight();
    f.fields = Arrays.copyOf(this.fields, this.fields.length);
    f.avgArrivalDelay = this.avgArrivalDelay;
    f.avgDepartureDelay = this.avgDepartureDelay;
    return f;
  }
  
  public Instant getEventTimestamp() {
    String timestamp = getField(INPUTCOLS.NOTIFY_TIME).replace('T', ' ');
    DateTime dt = fmt.parseDateTime(timestamp);
    return dt.toInstant();
  }
}
