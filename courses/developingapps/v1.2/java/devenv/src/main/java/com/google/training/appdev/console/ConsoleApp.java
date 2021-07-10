/*
 * Copyright 2018 Google Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.google.training.appdev.console;

import com.google.api.client.googleapis.auth.oauth2.GoogleCredential;
import com.google.api.client.googleapis.javanet.GoogleNetHttpTransport;
import com.google.api.client.http.HttpTransport;
import com.google.api.client.json.JsonFactory;
import com.google.api.client.json.jackson2.JacksonFactory;
import com.google.api.services.compute.Compute;
import com.google.api.services.compute.ComputeScopes;
import com.google.api.services.compute.model.AccessConfig;
import com.google.api.services.compute.model.AttachedDisk;
import com.google.api.services.compute.model.AttachedDiskInitializeParams;
import com.google.api.services.compute.model.Instance;
import com.google.api.services.compute.model.InstanceList;
import com.google.api.services.compute.model.Metadata;
import com.google.api.services.compute.model.NetworkInterface;
import com.google.api.services.compute.model.Operation;
import com.google.api.services.compute.model.ServiceAccount;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;


public class ConsoleApp {


  private static final String APPLICATION_NAME = "";

  /** Set PROJECT_ID to your Project ID from the Overview pane in the Developers console. */
  private static final String PROJECT_ID = System.getenv("GCLOUD_PROJECT");

  /** Set Compute Engine zone. */
  private static final String ZONE_NAME = "us-central1-f";

  
  /** Global instance of the HTTP transport. */
  private static HttpTransport httpTransport;

  /** Global instance of the JSON factory. */
  private static final JsonFactory JSON_FACTORY = JacksonFactory.getDefaultInstance();



  public static void main(String[] args) {
    try {
      httpTransport = GoogleNetHttpTransport.newTrustedTransport();

      // Authenticate using Google Application Default Credentials.
      GoogleCredential credential = GoogleCredential.getApplicationDefault();
      if (credential.createScopedRequired()) {
        List<String> scopes = new ArrayList<>();
        // Set Google Cloud Storage scope to Full Control.
        scopes.add(ComputeScopes.DEVSTORAGE_FULL_CONTROL);
        // Set Google Compute Engine scope to Read-write.
        scopes.add(ComputeScopes.COMPUTE);
        credential = credential.createScoped(scopes);
      }

      // Create Compute Engine object for listing instances.
      Compute compute =
          new Compute.Builder(httpTransport, JSON_FACTORY, credential)
              .setApplicationName(APPLICATION_NAME)
              .build();

      // List out instances
      printInstances(compute);

    } catch (IOException e) {
      System.err.println(e.getMessage());
    } catch (Throwable t) {
      t.printStackTrace();
    }
    System.exit(1);
  }

  // [START list_instances]
  /**
   * Print available machine instances.
   *
   * @param compute The main API access point
   * @return {@code true} if the instance created by this sample app is in the list
   */
  public static void printInstances(Compute compute) throws IOException {
    System.out.println("================== Listing Compute Engine Instances ==================");
    Compute.Instances.List instances = compute.instances().list(PROJECT_ID, ZONE_NAME);
    InstanceList list = instances.execute();
    if (list.getItems() == null) {
      System.out.println("No instances found. Sign in to the Google Developers Console and create "
          + "an instance at: https://console.developers.google.com/");
    } else {
      for (Instance instance : list.getItems()) {
        System.out.println(instance.toPrettyString());
      }
    }
  }
  // [END list_instances]

}