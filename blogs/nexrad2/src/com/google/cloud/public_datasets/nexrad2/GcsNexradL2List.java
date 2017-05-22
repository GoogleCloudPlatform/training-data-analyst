/*
 * Copyright (C) 2017 Google Inc.
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
package com.google.cloud.public_datasets.nexrad2;

import java.time.YearMonth;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import com.google.cloud.storage.Blob;
import com.google.cloud.storage.Storage;
import com.google.cloud.storage.Storage.BlobListOption;
import com.google.cloud.storage.StorageOptions;

/**
 * Finds list of tar files in NEXRAD Level 2 public data from GCS
 * 
 * @author vlakshmanan
 *
 */
public class GcsNexradL2List {
 
  public static List<String> getFiles(String radar, int year, int month, int day) {
    Storage storage = StorageOptions.getDefaultInstance().getService();
    String bucket = "gcp-public-data-nexrad-l2";
    String date = String.format("%d/%02d/%02d", year, month, day);
    Iterable<Blob> blobs = storage.list(bucket, BlobListOption.prefix(date + "/" + radar)).iterateAll();
    List<String> result = new ArrayList<>();
    for (Blob blob : blobs) {
      result.add("gs://" + blob.getBucket() + "/" + blob.getName());
    }
    return result;
  }

  public static List<String> getFiles(String radar, int year, int month) {
    // how many days in this month?
    YearMonth yearMonthObject = YearMonth.of(year, month);
    int maxday = yearMonthObject.lengthOfMonth();
    List<String> result = new ArrayList<String>();
    for (int day=1; day <= maxday; ++day) {
      result.addAll(getFiles(radar, year, month, day));
    }
    return result;
  }
  
  public static void main(String[] args) throws Exception {
    List<String> files = getFiles("KYUX", 2012, 7, 23);
    Collections.sort(files);
    System.out.println(files.size() + " files");
    System.out.println(" from " + files.get(0));
    System.out.println(" to " + files.get(files.size()-1));
  }
}
