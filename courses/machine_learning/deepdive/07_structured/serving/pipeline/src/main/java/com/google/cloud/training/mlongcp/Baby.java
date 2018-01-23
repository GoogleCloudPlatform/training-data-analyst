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

package com.google.cloud.training.mlongcp;

import java.util.Arrays;

import org.apache.beam.sdk.coders.AvroCoder;
import org.apache.beam.sdk.coders.DefaultCoder;

/**
 * @author vlakshmanan
 *
 */
@DefaultCoder(AvroCoder.class)
public class Baby {
  public enum INPUTCOLS {
    weight_pounds,is_male,mother_age,plurality,gestation_weeks,key;
  }

  private String[] fields;

  public static Baby fromCsv(String line) {
    Baby f = new Baby();
    f.fields = line.split(",");
    if (f.fields.length == INPUTCOLS.values().length) {
      return f;
    }
    return null; // malformed
  }
  
  public String[] getFields() {
    return fields;
  }

  public String getField(INPUTCOLS col) {
    return fields[col.ordinal()];
  }

  public float getFieldAsFloat(INPUTCOLS col) {
    return Float.parseFloat(fields[col.ordinal()]);
  }
  
  public int getFieldAsInt(INPUTCOLS col) {
    return Integer.parseInt(fields[col.ordinal()]);
  }
  
  public float getFieldAsFloat(INPUTCOLS col, float defaultValue) {
    String s = fields[col.ordinal()];
    if (s.length() > 0) {
      return Float.parseFloat(s);
    } else {
      return defaultValue;
    }
  }

  public Baby newCopy() {
    Baby f = new Baby();
    f.fields = Arrays.copyOf(this.fields, this.fields.length);
    return f;
  }

}
