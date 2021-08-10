# Demo: Monitoring of Batch and Streaming Pipelines in Dataflow

Goal: Give a overview of the monitoring tools in Dataflow for both batch and streaming pipelines via a hands-on examples. Both of the hands-on examples will use Dataflow templates for simplicity. This demo is not to replace the slides for the Monitoring, Logging and Error Reporting modules of the Dataflow course, but to rather augment these decks with a real example.

Note that there will not be many images for this demo and that we are expecting the person running the demo to be familiar with the Dataflow UI. This can be thought of as more of a checklist of things to show and explain.

## Demo Setup and Notes

The batch pipeline for this demo should be ran in advance for the sake of time. The streaming pipeline ideally should be running at demo time to show real-time metrics.

To create an output bucket in Cloud Storage (if needed) and run a word count pipeline from template, you can run the following commands in Cloud Shell

```bash
gsutil mb -l us-central1 gs://$DEVSHELL_PROJECT_ID
gcloud dataflow jobs run word_count_monitoring --gcs-location "gs://dataflow-templates-us-central1/latest/Word_Count" --region us-central1 --parameters inputFile=gs://dataflow-samples/shakespeare/kinglear.txt,output=gs://$DEVSHELL_PROJECT_ID
``` 

To start the streaming pipeline we will use, run the following commands to create a BigQuery sink dataset (which may already exist) and the pipeline

```bash
bq mk --location US dataflow_demos
INPUT_TOPIC=projects/pubsub-public-data/topics/taxirides-realtime
OUTPUT_TABLE=$DEVSHELL_PROJECT_ID:dataflow_demos.realtime
gcloud dataflow jobs run streaming-taxi-pipeline --gcs-location gs://dataflow-templates-us-central1/latest/PubSub_to_BigQuery --region us-central1 --staging-location gs://$DEVSHELL_PROJECT_ID --parameters inputTopic=$INPUT_TOPIC,outputTableSpec=$OUTPUT_TABLE
```

Note that we will be using the streaming pipeline to get into some concepts around logging and error reporting. The output table should not exist at the time of running this template (so we can diagnose the error in real-time). To confirm this run the following command:

```bash
bq rm -f -t $OUTPUT_TABLE
```
One can create the table later if you wish during the demo to resolve the backlog

```bash 
bq mk --table $DEVSHELL_PROJECT_ID:dataflow_demos.realtime ride_id:STRING,point_idx:INTEGER,latitude:FLOAT,longitude:FLOAT,timestamp:STRING,meter_reading:FLOAT,meter_increment:FLOAT,ride_status:STRING,passenger_count:INTEGER
```

## Batch Pipeline Monitoring

In advance we ran a pipeline to perform a Word Count job on a text file in Cloud Storage. We can go to the UI and explore some of the pieces of this pipeline. Go to the Cloud Console and then to **Dataflow >> Jobs**. Select the job *word_count_monitoring*. A lot of these details we have seen before. For example we can see the job graph, the job info (containing metadata and other information about the job), the resource metrics for resources consumed by the job, and finally the pipeline options which were passed to the pipeline job. Also note that we can see a custom metric (the `emptyLines` counter) as well on the right-hand side of the UI. Note that we can see where this is defined in the [Word Count template](https://github.com/GoogleCloudPlatform/DataflowTemplates/blob/master/src/main/java/com/google/cloud/teleport/templates/WordCount.java) starting at line 43:

```java
  static class ExtractWordsFn extends DoFn<String, String> {
    private final Counter emptyLines = Metrics.counter(ExtractWordsFn.class, "emptyLines");

    @ProcessElement
    public void processElement(ProcessContext c) {
      if (c.element().trim().isEmpty()) {
        emptyLines.inc();
      }
      
   \\ Rest of code omitted
   
```

We can see the line of code `private final Counter emptyLines = Metrics.counter(ExtractWordsFn.class, "emptyLines");` defining the `emptyLines` counter metric and the line `emptyLines.inc();` which when executed increments the counter.

We can click on the steps to expand (if they represent composite PTransforms) and look at information about the individual step of the pipeline.

Let's click on the `WordCount.CountWords` step, when we expand it we can see two transforms `ParDo(ExtractWords)` and `Count.PerElement`. On the right-hand side of the UI you can see the information about the step. This includes the wall time (Approximate time spent in this step on initializing, processing data, shuffling data, and terminating, across all threads in all workers.), infromation about input and output PCollections (including throughput) and the stages involved in the step. We will come back and talk about the distinction between steps and stages later when discussing performance for Dataflow pipelines.

We can also click on the **Job Metrics** tab to see metrics such as Autoscaling, throughput per step, and worker error log count.

## Stream Pipeline Monitoring

Now, let us explore a streaming pipeline. Go back to the main **Jobs** menu (either by hitting the back button or going back to **Dataflow > Jobs**. Select the job *streaming-taxi-pipeline*.

For the most part, the UI is similar to the case of the batch processing job. However, let us point out some of the differences.

First, notice that on the right-hand side of the UI, we can see that the "Job Type" of the job is streaming. Recall that we set an option for our pipeline to determine if the pipeline is either batch or streaming.

Now click on the **Job Metrics** tab, notice that we have two new metrics here. First we have the "Data freshness", which is defined as the number of seconds since the most recent watermark. We also have the "System latency", which is defined as the number of seconds that an item of data has been processing or waiting inside any one pipeline source.

However...notice that both the data freshness and system latency are strictly increasing over time! This is a big red flag that something isn't quite working as intended with our streaming pipeline. 

At the bottom of the UI, notice that we see a tab for Logs. We also see a red circle with an exclaimation point (with some number) representing that we have errors in the pipeline. We can click on the logs to explore and see if we can narrow down the issue.

If we look more carefully, we see the error:

`Error message from worker: java.lang.RuntimeException: com.google.api.client.googleapis.json.GoogleJsonResponseException: 404 Not Found POST https://bigquery.googleapis.com/bigquery/v2/projects/maabel-testground/datasets/dataflow_demos/tables/realtime/insertAll?prettyPrint=false { "code" : 404, "errors" : [ { "domain" : "global", "message" : "Not found: Table maabel-testground:dataflow_demos.realtime", "reason" : "notFound" } ], "message" : "Not found: Table maabel-testground:dataflow_demos.realtime", "status" : "NOT_FOUND" }`

We see that the table was not found (and if we dived into the template code, we would see that the table create disposition is not "CREATE_IF_NEEDED")! So the pipeline was able to process the data coming in from Pub/Sub, but did not have a sink to write to. We can easily fix this error by creating the table with the correct schema.

However, we only found out about this problem by manually going in and exploring the metrics and logs. In practice, we often want to set up alerts with Error Reporting and/or Monitoring to let us know when something is not performing as intended.

Let us set up an alert for data freshness so we can tell if the pipeline is getting behind. That way we know to come and take a look and try to understand what is going on. Above the graph for data freshness, click on "Create alerting policy". This will take us to Cloud Monitoring so that we can set up our alerting policy.

A lot of what we want to creating the alerting policy for "Data watermark lag" is already populated for us. Scroll down to Configuration and put select/input the following information to finish setting up the alerting policy:

* Condition triggers if: "any time series violates"
* Condition: "is above"
* Threshold: 300
* For: "5 minutes"

If our watermark lag remains above 5 minutes for a span of 5 minutes, then we will send out an alert to ensure that someone takes a closer look at the pipeline.

Click **Save** to save the alert, then click **Next**. Here we can choose a notification channel to send out the alert and then click **Next** to input text to send along with the alert. This way, whoever is assigned to manage the alert will know what the alert is for.







