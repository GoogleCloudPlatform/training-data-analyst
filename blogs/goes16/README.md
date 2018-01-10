## Accessing GOES-16 data from Python

This repository contains example code of accessing GOES-16 data from Python from a Google Compute Engine instance or using Python Dataflow.

* Python from a Compute Engine instance
  * Create a Compute Engine instance from the GCP console
  * Git clone this repository on that machine and install the necessary software (this takes a while):
  ```
  sudo apt-get install git
  git clone https://github.com/GoogleCloudPlatform/training-data-analyst
  cd training-data-analyst/blogs/goes-16/maria
  bash install.sh
  ```
  * Run a command-line program to create a single image of Hurricane Maria early in its lifecycle:
  ```
  python create_image.py --outdir /tmp/image --year 2017
  ```
* Python Dataflow to parallelize processing
  * If you haven't already done so, git clone this repository and install the necessary software  (this takes a while):
  ```
  sudo apt-get install git
  git clone https://github.com/GoogleCloudPlatform/training-data-analyst
  cd training-data-analyst/blogs/goes-16/maria
  bash install.sh
  ```
  * Launch off a Python Dataflow job to create images corresponding to the track of Hurricane Maria:
  ```
  python create_image.py --bucket YOUR_BUCKET --project $(gcloud config get-value project) --hurricane Maria --year 2017
  ```
  Monitor progress in the Dataflow section of the GCP web console.
  * Launch off a Python Dataflow job to create images corresponding to the all the hurricanes in the North Atlantic basin
  ```
  python create_image.py --bucket YOUR_BUCKET --project $(gcloud config get-value project) --basin NA --year 2017
  ```
  Monitor progress in the Dataflow section of the GCP web console.

See [TBD](this blog post) for details on what the Python code above is doing.

## Getting notified about new files: Pub/Sub
* In CloudShell, or in another enviroment where the gcloud SDK is installed:
  * Run 
  ```
  gcloud beta pubsub subscriptions create testsubscription \
      --topic=projects/gcp-public-data---goes-16/topics/gcp-public-data-goes-16
  ```
  to create a subscription. As new GOES files are added to the public data bucket, details about the files will populate
  this subscription. The messages will persist until you consume the message (to a maximum of 7 days)
  * Consume one message and pull out objectId
  ```
  gcloud beta pubsub subscriptions pull testsubscription | tr ' ' '\n' | grep objectId
  ```
  It is likely that the number of messages will be zero the first time. Wait a couple of minutes until you can reasonably
  expect that the bucket will contain new files. You will be notified only about files added to the bucket after the
  subscription was created.
  * Once you get a objectId, you can verify that the file exists. For example, let's say you got this:
   ```
   objectId=ABI-L2-MCMIPF/2017/306/21/OR_ABI-L2-MCMIPF-M4_G16_s20173062105222_e20173062110034_c20173062110127.nc
   ```
   Then, you can verify that it exists using:
   ```
   gsutil ls -l gs://gcp-public-data-goes-16/ABI-L2-MCMIPF/2017/306/21/OR_ABI-L2-MCMIPF-M4_G16_s20173062105222_e20173062110034_c20173062110127.nc
   ```
  * Delete the subscription using [./delete_subscription.sh](./delete_subscription.sh) or by typing in:
  ```
  gcloud beta pubsub subscriptions delete testsubscription
  ```

## Processing files routinely with Dataflow-Java
This repo also contains [an example of how you can write a Apache Beam pipeline](./src/src/com/google/cloud/public_datasets/goes16/ListenPipeline.java) to create a subscription, monitor the topic, and do some processing of the files. The key code is:
```
      .apply("ReadMessage", PubsubIO.readStrings().fromTopic(topic)) //
      .apply("ParseMessage", ParDo.of(new DoFn<String, String>() {
        @ProcessElement
        public void processElement(ProcessContext c) throws Exception {
          String message = c.element();
          String[] fields = message.split(" ");
          for (String f : fields) {
            if (f.startsWith("objectId=")) {
              String objectId = f.replace("objectId=", "");
              c.output("gs://gcp-public-data-goes-16/" + objectId);
            }
          }
        }
      })) //
      .apply("ProcessFile", ParDo.of(new DoFn<String, String>() {
        @ProcessElement
        public void processElement(ProcessContext c) throws Exception {
          String gcsFileName = c.element();
          log.info("Processing " + gcsFileName);
          // YOUR CODE to actually process the file would go here
        }
      }));
```
Monitor progress in the Dataflow section of the GCP web console and stop the job when no longer required.
 
## Processing files routinely with Python-Dataflow

This repo also contains [an example of how you can write a Apache Beam pipeline](./maria/create_seattle.py) to create a subscription, monitor the topic, and do some processing of the files. The key code is for the pipeline to read from Pub/Sub rather than BigQuery or a text file:

  ```
  beam.io.ReadStringsFromPubSub('projects/{}/topics/{}'.format(
                                  'gcp-public-data---goes-16',
                                   'gcp-public-data-goes-16'))
  ```

* Here's an example of creating png images of the IR channel around a specific lat-lon in real-time
  * If you haven't already done so, git clone this repository and install the necessary software  (this takes a while):
  ```
  sudo apt-get install git
  git clone https://github.com/GoogleCloudPlatform/training-data-analyst
  cd training-data-analyst/blogs/goes-16/maria
  bash install.sh
  ```
  * Launch off a Python Dataflow job to create images in real-time
  ```
  python create_seattle.py --bucket YOUR_BUCKET --project $(gcloud config get-value project) --lat 47.61 --lon -122.33
  ```
  Monitor progress in the Dataflow section of the GCP web console and stop the job when no longer required.
