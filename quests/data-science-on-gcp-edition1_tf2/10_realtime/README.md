# 10. Real-time machine learning

### [optional] Setup Dataflow Development environment
To develop Apache Beam pipelines in Eclipse:
* Install the latest version of the Java SDK (not just the runtime) from http://www.java.com/
* Install Maven from http://maven.apache.org/
* Install Eclipse for Java Developers from http://www.eclipse.org/
* If you have not already done so, git clone the respository:
    ```
    git clone https://github.com/GoogleCloudPlatform/data-science-on-gcp
    ```
* Open Eclipse and do File | Import | From existing Maven files.
  Browse to, and select `data-science-on-gcp/10_realtime/chapter10/pom.xml`
* Edit the PROJECT in to reflect your project.
* You can now click on any Java file with a `main()` (e.g: `FlightsMLService.java`) and select Run As | Java Application.


### Invoking prediction service
* Edit the PROJECT setting in:
  `10_realtime/chapter10/src/main/java/com/google/cloud/training/flights/FlightsMLService.java`
* In CloudShell, try out the service using Maven:
  ```
     cd data-science-on-gcp/10_realtime/chapter10
     mvn compile exec:java -Dexec.mainClass=com.google.cloud.training.flights.FlightsMLService
  ```
### Run streaming pipeline to add predictions to flight information
In CloudShell:
* Install the necessary packages and provide the simulation code authorization to access your BigQuery dataset:
  ```
     ../04_streaming/simulate/install_packages.sh
     gcloud auth application-default login
  ```  
* Go to the Pub/Sub section of the GCP console and create a temporary Pub/Sub topic `dataflow_temp` for Dataflow to use.
* Start the simulation:
  ```
     ./simulate.sh
  ``` 
* Open a second CloudShell tab, and authenticate again within this tab:
  ```
     cd data-science-on-gcp/10_realtime
     gcloud auth application-default login
  ``` 
* In the second CloudShell tab, launch the Dataflow pipeline:
  ```
     ./predict.sh bucket-name project-id
  ```  
* Visit https://console.cloud.google.com/dataflow to monitor the running pipeline.
  If the pipeline fails due to insufficient quota, go to https://cloud.google.com/compute/quotas and
  clean up all unused resources, and if that still isn't enough, request the appropriate quota increase.
  Once you see elements being written into Bigquery, go to next step.

* From the GCP console, go to BigQuery and run this query:
    ```
    SELECT * from flights.predictions ORDER by notify_time DESC LIMIT 5
    ```

* To play around with jitter options, change `./simulate.sh` and edit the `--jitter` argument.
  The graphs in the chapter come from `distributions.ipynb`.

* <b>Important</b> Because this is a streaming pipeline, it will keep running. You have to stop it.
  * Go to the Dataflow console and stop the streaming job.
  * Stop the simulation in CloudShell.

   
### [optional] Low-latency with Bigtable
In CloudShell:
* Create a Bigtable instance:
  ```
     cd data-science-on-gcp/10_realtime
     ./create_cbt.sh
  ```  
* Install the necessary packages and provide the simulation code authorization to access your BigQuery dataset:
  ```
     ../04_streaming/simulate/install_packages.sh
     gcloud auth application-default login
  ```  
* Start the simulation:
  ```
     ./simulate.sh
  ``` 
* Open a second CloudShell tab, and authenticate again within this tab:
  ```
     cd data-science-on-gcp/10_realtime
     gcloud auth application-default login
  ``` 
* In the second CloudShell tab, launch the Dataflow pipeline:
  ```
     ./predict_bigtable.sh bucket-name project-id
  ```  
* Visit https://console.cloud.google.com/dataflow to monitor the running pipeline.
  If the pipeline fails due to insufficient quota, go to https://cloud.google.com/compute/quotas and
  clean up all unused resources, and if that still isn't enough, request the appropriate quota increase.
  Because this is a real-time pipeline that streams into Bigtable, the required resources might exceed
  what you might be able to do on the free tier.
  Once you see elements being written into Bigtable, go to next step.

* Query Bigtable:
  * Install and run HBase quickstart by:
    ```
    ./install_quickstart.sh
    cd quickstart
    ./quickstart.sh
    ```
  * Type in a query:
  ```
  scan 'predictions', {STARTROW => 'ORD#LAX#AA', ENDROW => 'ORD#LAX#AB', COLUMN => ['FL:ontime','FL:EVENT'], LIMIT => 2}
  ```
  * Type `quit` to exit the prompt.

* <b>Important</b> Cleanup both the streaming job and the Bigtable instance.
  * Go to the Dataflow console and stop the streaming job.
  * Stop the simulation in CloudShell.
  * Delete your Bigtable instance:
  ```
     ./delete_cbt.sh
  ```

### Evaluate model performance
* Ingest 2016 data to carry out the evaluation on.
    ```
    cd ~/data-science-on-gcp/10_realtime
    ./ingest_2016.sh bucket-name
    ```
* Run the program to correct the timestamps:
   ```
    cd ~/data-science-on-gcp/04_streaming/simulate
    bq mk flights2016
    ./install_packages.sh
    ./df06.py --project=$DEVSHELL_PROJECT_ID --dataset=flights2016 --bucket=BUCKETNAME 
   ```
* Monitor the job in the Dataflow section of the GCP console.
* Once it is finished, run the Dataflow pipeline to do the evaluation:
    ```
    cd ~/data-science-on-gcp/10_realtime
    ./eval.sh bucket-name project-id
    ```
* Monitor the job in the Dataflow section of the GCP console.
* Once it is finished, load the evaluation data into BigQuery.
   ```
    cd ~/data-science-on-gcp/10_realtime
    ./to_bq.sh bucket-name
    ```
