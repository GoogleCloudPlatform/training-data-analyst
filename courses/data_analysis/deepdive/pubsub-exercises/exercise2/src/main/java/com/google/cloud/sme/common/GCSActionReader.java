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

import com.google.cloud.ReadChannel;
import com.google.cloud.sme.Entities;
import com.google.cloud.storage.Blob;
import com.google.cloud.storage.BlobId;
import com.google.cloud.storage.Storage;
import com.google.cloud.storage.StorageOptions;
import java.io.BufferedReader;
import java.nio.ByteBuffer;
import java.nio.channels.Channels;

/** Reads a sequence of actions from a CSV file stored in GCS. */
public class GCSActionReader implements ActionReader {
  private BlobId fileId;
  private BufferedReader actionReader = null;
  private ByteBuffer buffer;
  private int bufferPosition;
  private int bufferLength;

  public GCSActionReader(String bucketName, String fileName) {
    this.fileId = BlobId.of(bucketName, fileName);
  }

  private void openFile() {
    Storage storage = StorageOptions.getDefaultInstance().getService();
    Blob file = storage.get(fileId);
    ReadChannel reader = file.reader();
    actionReader = new BufferedReader(Channels.newReader(reader, "UTF-8"));
  }

  @Override
  public Entities.Action next() {
    String line;
    try {
      if (actionReader == null) {
        openFile();
      }
      line = actionReader.readLine();
    } catch (Exception e) {
      System.out.println("Could not read from " + fileId + ": " + e);
      return null;
    }

    if (line == null) {
      return null;
    }
    return ActionUtils.parseFromCSVLine(line);
  }
}
