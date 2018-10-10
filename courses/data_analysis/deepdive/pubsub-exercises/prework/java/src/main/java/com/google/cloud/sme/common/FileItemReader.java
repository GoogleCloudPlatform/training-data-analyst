// Copyright 2017 Google Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
////////////////////////////////////////////////////////////////////////////////
package com.google.cloud.sme.common;

import com.google.cloud.sme.Entities;
import java.io.BufferedReader;
import java.io.FileReader;

/** Reads a sequence of items from a local CSV file. */
public class FileItemReader implements ItemReader {
  private String fileName;
  private BufferedReader itemReader = null;

  public FileItemReader(String fileName) {
    this.fileName = fileName;
  }

  @Override
  public Entities.Item next() {
    String line;
    try {
      if (itemReader == null) {
        itemReader = new BufferedReader(new FileReader(fileName));
      }
      line = itemReader.readLine();
    } catch (Exception e) {
      System.out.println("Could not read from " + fileName + ": " + e);
      return null;
    }

    if (line == null) {
      return null;
    }
    return ItemUtils.parseFromCSVLine(line);
  }
}
