# Demo: Comparison of Trigger Behaviors

Goal: Give a simple, quick demo to show how the emitted results for the two possible accumulation modes compare. 

## Demo Setup and Notes

This demo can ran in advance for the sake of time. This is a streaming pipeline, so it is important to be sure to remember to stop the pipeline to prevent additional costs. In this setup we include the pipeline shutdown as part of the demo setup

Included in this folder is an Apache Beam pipeline to run on Dataflow named `trigger_demo_pipeline.py`. This pipeline will be ran twice to show the differences between `ACCUMULATING` and `DISCARDING` accumulation modes

First clone the repo (if you have not already)

```bash
git clone https://github.com/GoogleCloudPlatform/training-data-analyst
```

and the set your environment variables and create a GCS bucket and BigQuery dataset if needed

```bash
cd ./training-data-analyst/courses/dataflow/demos/triggers

PROJECT_ID=$(gcloud config get-value project)
REGION=us-central1
BUCKET=gs://$PROJECT_ID-df-demo

gsutil mb -l us-central1 $BUCKET
bq mk --location=US dataflow_demos
```

Run the first pipeline in Cloud Shell (or your development envrionment) using the following command

```bash
python3 trigger_demo_pipeline.py \
    --project=$PROJECT_ID \
    --region=$REGION \
    --staging_location=$BUCKET/staging \
    --temp_location=$BUCKET/temp \
    --streaming \
    --accum_mode=accumulating
```

This first pipeline will use the ACCUMULATING accumulation mode. Also start a second pipeline using the DISCARDING accumulation mode by running the following command

```bash
python3 trigger_demo_pipeline.py \
    --project=$PROJECT_ID \
    --region=$REGION \
    --staging_location=$BUCKET/staging \
    --temp_location=$BUCKET/temp \
    --streaming \
    --accum_mode=discarding
```

The Dataflow jobs will have the names `accumulating-<timestamp>` and `discarding-<timestamp>` respectively.

Wait around 10 minutes for data to be processed and written to BigQuery, and then be sure to stop both pipelines. You can stop a pipeline by going to **Dataflow > Jobs** and clicking on the job name. Above the pipeline in the UI is a button **Stop**.

## Walkthrough

In this demo we have already ran two pipelines to count simulated real-time taxi ride events with the exact same data source and processing logic, with the exception of the accumulation mode. Let's take a look at the pipeline itself and then we will go to BigQuery and compare the results.

```python
    input_topic = "projects/pubsub-public-data/topics/taxirides-realtime"
    output_table = f"{opts.project}:dataflow_demos.{opts.accum_mode}"

    if opts.accum_mode == 'accumulating':
        accum_mode = beam.transforms.trigger.AccumulationMode.ACCUMULATING
    elif opts.accum_mode == 'discarding':
        accum_mode = beam.transforms.trigger.AccumulationMode.DISCARDING
    else:
        raise ValueError('Invalid accumulation mode value. Use \'accumulating\' or \'discarding\' ')

    p = beam.Pipeline(options=options)

    (p | 'ReadFromPubSub' >> beam.io.ReadFromPubSub(input_topic)
       | 'ParseJson' >> beam.Map(parse_json).with_output_types(TaxiRide)
       | 'WindowByMinute' >> beam.WindowInto(beam.window.FixedWindows(60),
                                              trigger=AfterWatermark(early=AfterProcessingTime(10)),
                                              accumulation_mode=accum_mode)
       | "CountPerMinute" >> beam.CombineGlobally(CountCombineFn()).without_defaults()
       | "AddWindowTimestamp" >> beam.ParDo(GetTimestampFn())
       | 'WriteAggToBQ' >> beam.io.WriteToBigQuery(
            output_table,
            schema=table_schema,
            create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
            write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND
            )
    )
```

First, we will read from a public Pub/Sub topic simulating real-time taxiride events. The messages are recieved in the JSON format, so we will parse the JSON blobs into objects of type `TaxiRide`. After that we will window the data by minute, but emit early results every 10 seconds. The big difference between the two pipeline runs is if the pipeline will use the `ACCUMULATING` or the `DISCARDING` accumulation mode. This information was passed in as a command-line argument.

After applying the windowing logic, we will count the number of taxi rides in each window (emitting results per the triggering rules) and then write out to BigQuery after attaching the starting timestamp for each window.

Now let's go to BigQuery to see how the results differ.

First let us run a query to get a timestamp to use

```sql
SELECT
  *
FROM
  `dataflow_demos.accumulating`
ORDER BY
  timestamp DESC
```

To be safe (assuming that the pipeline is still running or that you cancelling the pipeline runs at similar times) choose a timestamp a few rows down. For the run this demo is based off of, the timestamp chosen was `'2021-06-03T21:15:00'`. For the following queries, replace this timestamp with your own.

Next we want to look at the results for each window. First let's look at the results for the ACCUMULATING accumulation mode.

```sql
SELECT
  *
FROM
  `dataflow_demos.accumulating`
WHERE
  timestamp = '2021-06-03T21:15:00'
ORDER BY taxi_events DESC
```

The results should look like the following:

| Row | taxi_events | timestamp           |
|-----|------------|---------------------|
| 1   |      52076 | 2021-06-03T21:15:00 |
| 2   |      51769 | 2021-06-03T21:15:00 |
| 3   |      42655 | 2021-06-03T21:15:00 |
| 4   |      36346 | 2021-06-03T21:15:00 |
| 5   |      29322 | 2021-06-03T21:15:00 |
| 6   |      16640 | 2021-06-03T21:15:00 |
| 7   |      13048 | 2021-06-03T21:15:00 |
| 8   |       4108 | 2021-06-03T21:15:00 |

Notice a few things:
* We have more than 6 results, even though we were working with an early trigger every 10 seconds with 60 second windows...why? We are emitting results every 10 seconds in *processing time* but closing the window after 60 seconds of *event time*. Thus depending on the watermark, the window may be kept open longer than 60 seconds.
* The results are monotonically increasing.

Now let's look at the same timestamp, but for the discarding table.

```sql
SELECT
  *
FROM
  `dataflow_demos.discarding`
WHERE
  timestamp = '2021-06-03T21:15:00'
ORDER BY taxi_events DESC
```

| Row | taxi_events | timestamp           |
|-----|------------|---------------------|
| 1   |      10448 | 2021-06-03T21:15:00 |
| 2   |      10074 | 2021-06-03T21:15:00 |
| 3   |       9520 | 2021-06-03T21:15:00 |
| 4   |       9022 | 2021-06-03T21:15:00 |
| 5   |       8572 | 2021-06-03T21:15:00 |
| 6   |       3312 | 2021-06-03T21:15:00 |
| 7   |       1128 | 2021-06-03T21:15:00 |
| 8   |          0 | 2021-06-03T21:15:00 | 

This is still monotonically increasing...but of course this is the case because of the ORDER BY statement! The bigger thing to notice is that the numbers are much smaller. This is because after a result is emitted, we clear the state in DISCARDING mode.

Do we get the same information in the end? For ACCUMULATING with a count, we expect the largest number to be the total count. However, for DISCARDING, we expect the sum of the counts to add up to the total. Let's confirm.

```sql
SELECT
  SUM(page_views) as event_count, 'discarding' as mode
FROM
  `dataflow_demos.discarding`
WHERE
  timestamp = '2021-06-03T21:15:00'
UNION ALL
SELECT
  MAX(page_views) as event_count, 'accumulating' as mode
FROM
  `dataflow_demos.accumulating`
WHERE
  timestamp = '2021-06-03T21:15:00'
```

| Row | event_count | mode         |
|-----|-------------|--------------|
| 1   |       52076 | accumulating |
| 2   |       52076 | discarding   |

As expected the two results are the same.

