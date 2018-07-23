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

import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.ByteBuffer;
import java.util.ArrayList;
import java.util.List;

import org.apache.commons.compress.archivers.ArchiveException;
import org.apache.commons.compress.archivers.ArchiveStreamFactory;
import org.apache.commons.compress.archivers.tar.TarArchiveEntry;
import org.apache.commons.compress.archivers.tar.TarArchiveInputStream;
import org.apache.commons.compress.utils.IOUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.google.cloud.ReadChannel;
import com.google.cloud.storage.Storage;
import com.google.cloud.storage.StorageOptions;
import com.google.common.io.Files;

/**
 * Provides the ability to read a tar file from Google Cloud Storage. This class
 * creates some temporary directories that it cleans up when closed, so do not
 * use the provided data outside the scope of this object:
 * 
 * <pre>
    String tarFile = "gs://gcp-public-data-nexrad-l2/2016/05/03/KAMA/NWS_NEXRAD_NXL2DP_KAMA_20160503000000_20160503005959.tar";
    try (GcsUntar untar = GcsUntar.fromGcsOrLocal(tarFile)) {
      for (File f : untar.getFiles()) {
        System.out.println(f.getName());
        // do something with the file
      }
    }
    </pre>
 * 
 * @author vlakshmanan
 *
 */
public class GcsUntar implements AutoCloseable {
  private static final Logger log = LoggerFactory.getLogger(GcsUntar.class);

  private final File tarFileLocation;
  private final File   tempDirectory;
  private File[]   untarred;

  private GcsUntar(File tarFileLocation, File tempDirectory)  {
    this.tarFileLocation = tarFileLocation;
    this.tempDirectory = tempDirectory;
  }

  public static GcsUntar fromLocalTar(File tarFileName) {
    return new GcsUntar(tarFileName, Files.createTempDir());
  }

  public static GcsUntar fromGcsTar(String bucket, String blobName) throws IOException {
    File tmpDir = Files.createTempDir();
    File localFile = downloadFromGcs(bucket, blobName, tmpDir);
    return new GcsUntar(localFile, tmpDir);
  }
  
  public static GcsUntar fromGcsOrLocal(String gcsOrLocal) throws IOException {
    final String PROTOCOL = "gs://";
    if (gcsOrLocal.startsWith(PROTOCOL)) {
      // parse google cloud storage URL
      int bucketStart = PROTOCOL.length();
      int bucketEnd = gcsOrLocal.indexOf('/', bucketStart);
      String bucket = gcsOrLocal.substring(bucketStart, bucketEnd);
      String blobName = gcsOrLocal.substring(bucketEnd+1);
      return fromGcsTar(bucket, blobName);
    } else {
      // local
      return fromLocalTar(new File(gcsOrLocal));
    }
  }
  
  public File[] getFiles() throws IOException {
    if (untarred == null) {
      try {
        untarred = unTar(tarFileLocation, tempDirectory);
      } catch (ArchiveException e) {
        new IOException(e);
      }
    }
    return untarred;
  }

  private static File downloadFromGcs(String bucketName, String blobName, File tmpDir) throws IOException {
    Storage storage = StorageOptions.getDefaultInstance().getService();
    File fileName = File.createTempFile("download", "bytes", tmpDir);
    try (ReadChannel reader = storage.reader(bucketName, blobName);
        FileOutputStream writer = new FileOutputStream(fileName)) {
      ByteBuffer bytes = ByteBuffer.allocate(64 * 1024);
      while (reader.read(bytes) > 0) {
        bytes.flip();
        writer.getChannel().write(bytes);
        bytes.clear();
      }
    }
    return fileName;
  }
  
  private static File[] unTar(final File inputFile, final File outputDir)
      throws FileNotFoundException, IOException, ArchiveException {
    // from
    // http://stackoverflow.com/questions/315618/how-do-i-extract-a-tar-file-in-java/7556307#7556307
    log.info("tar xf " + inputFile + " to " + outputDir);
    final List<File> untaredFiles = new ArrayList<File>();
    final InputStream is = new FileInputStream(inputFile);
    final TarArchiveInputStream debInputStream = (TarArchiveInputStream) new ArchiveStreamFactory()
        .createArchiveInputStream("tar", is);
    TarArchiveEntry entry = null;
    while ((entry = (TarArchiveEntry) debInputStream.getNextEntry()) != null) {
      final File outputFile = getOutputFile(outputDir, entry);
      if (entry.isDirectory()) {
        if (!outputFile.exists()) {
          if (!outputFile.mkdirs()) {
            throw new IllegalStateException(
                String.format("Couldn't create directory %s.", outputFile.getAbsolutePath()));
          }
        }
      } else {
        final OutputStream outputFileStream = new FileOutputStream(outputFile);
        IOUtils.copy(debInputStream, outputFileStream);
        outputFileStream.close();
      }
      untaredFiles.add(outputFile);
    }
    debInputStream.close();

    return untaredFiles.toArray(new File[0]);
  }

  private static File getOutputFile(final File outputDir, TarArchiveEntry entry) 
      throws IOException, ArchiveException {
    // Guard against zip-slip-vulnerability: 
    // https://snyk.io/research/zip-slip-vulnerability#what-action-should-you-take
    final String canonicalDestinationDir = outputDir.getCanonicalPath();
    final File outputFile = new File(outputDir, entry.getName());
    final String canonicalDestinationFile = outputFile.getCanonicalPath();
    if (!canonicalDestinationFile.startsWith(canonicalDestinationDir)) {
      throw new ArchiveException("Entry " + entry.getName() + " is outside destination directory. " + 
          "See https://snyk.io/research/zip-slip-vulnerability");
    }
    return outputFile;
  }

  @Override
  public void close() throws Exception {
    log.info("rm -rf " + tempDirectory);
    rmdirWithoutSymbolicLinks(tempDirectory);
  }

  private static void rmdirWithoutSymbolicLinks(File dir) {
    // delete contents recursively
    for (File f : dir.listFiles()) {
      if (f.isDirectory()) {
        rmdirWithoutSymbolicLinks(f);
      } else {
        f.delete();
      }
    }
    dir.delete();
  }

  public static void main(String[] args) throws Exception {
    String tarFile = "/Users/vlakshmanan/data/nexrad/2016%2F05%2F03%2FKAMA%2FNWS_NEXRAD_NXL2DP_KAMA_20160503090000_20160503095959.tar";
    // String tarFile = "gs://gcp-public-data-nexrad-l2/2016/05/03/KAMA/NWS_NEXRAD_NXL2DP_KAMA_20160503000000_20160503005959.tar";
      
    System.out.println("Reading " + tarFile);
    try (GcsUntar untar = GcsUntar.fromGcsOrLocal(tarFile)) {
      for (File f : untar.getFiles()) {
        System.out.println(f.getName());
      }
    }
  }

}
