# Serverless ELT Pipelines using Cloud Functions

In this demo, we will discuss how we can use Cloud Functions to run an periodically-scheduled ELT pipeline to download Virginia COVID-19 ZIP Code level case data from the Virginia DOH website and upload to a table in BigQuery. Cloud Functions does not directly support scheduling, but it does support triggers based off a Pub/Sub message. We will also configure Cloud Scheduler to publish a message to a chosen topic once an hour to trigger our Cloud Function.

## Demo Setup

First we need to set up a few resources for the demo. All of this can be done using the Google Cloud SDK in Cloud Shell. 

1. Create a Pub/Sub topic to use as a trigger for the Cloud Function ``` gcloud pubsub topics create cron-hourly```
1. Create a BigQuery dataset in the US for the data we will be ingesting ``` bq mk -location=US -d  covid19 ```

## Cloud Scheduler

We will be creating a periodically-schedlued Cloud Function to download, transform, and ingest COVID-19 data into BigQuery. Cloud Scheduler will allow us to create a fully-managed cron job to publish a message to Pub/Sub hourly. We will configure Cloud Functions to listen for this trigger and execute the Cloud Function.

1. Go to the search bar at the top of the UI, and type in "Cloud Scheduler" and then click on the first result.
1. Click the "Create Job" button to create a Cloud Scheduler job.
1. Name the job "Hourly Cron Task"
1. Enter `0 * * * *` for the frequency. This is cron syntax that represents an hourly job.
1. Choose ""Eastern Standard Time (EST)"" or Eastern Daylight Time (EDT)" for the timezone.
1. Choose "Pub/Sub" as the target. Enter `cron-hourly` as the topic and `.` as the payload. 

Go ahead and hit "Create" to create and start the job.

## Cloud Functions

Now we will create our Cloud Function for our pipeline. We will configure the Cloud Function to listen for messages published by the Cloud Scheduler job we just created and then execute the function. Cloud Functions will deploy our function (as a container) within milliseconds and execute the Python script. Within 30 seconds, the job will be finished and there will be no infrastructure to shut down. Everything is fully-managed behind the scenes by Google Cloud.

1. Go to the search bar at the top of the UI, and type in "Cloud Functions" and then click on the first result.
1. Click on "Create Function".
1. Name the function "va-covid-by-zip" and select "us-central1" as the region.
1. Change the trigger type to "Cloud Pub/Sub" and input "cron-hourly" as the topic. Then click "Save" and then "Next".
1. For Runtime choose "Python 3.7" and make the entry point "update_va_covid".
1. Copy and paste the contents of the `main.py` file in this directory into the `main.py` file in your Cloud Function.
1. Repeat this process for the `requirements.txt` file.
1. Click "Deploy"

Everything is now set up! It will take a couple of minutes to deploy the Cloud Function. Cloud Functions is packaging the function into a container (via Cloud Build) and store the container in Google Container Registry. As the function is invoked it will deploy the containerized function within milliseconds.

Once the function is deployed, then we should test it. Click on the function and then the "Testing" tab. Once there click "Test The Function". The function will take around 15-20 seconds to run.

Once the function completes running, you can scroll down to see the "OK" status message and the logs (stored in Cloud Operations Logging). You will see a log of the form "Loaded 88316 rows and 6 columns to your-project-id.covid19.va_covid_data_by_zip" letting you know that everything was uploaded to BigQuery successfully!
