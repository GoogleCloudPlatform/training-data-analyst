# Setup for AutoML Tables Demo
Goal: Set up a demo for creating a custom regression model on structured data to predict NYC Yellow Taxi fares using [AutoML Tables](https://cloud.google.com/automl-tables/docs/). The script for this demo is adapted from a recorded demo of AutoML Tables.

**Note:** This is a demo you need to set up in advance if you want to present it. Loading the data into AutoML Tables takes 15-20 minutes and it will take a few hours to train the model. It is recommended having the dataset preloaded and model trained for a live demo. Also be careful with leaving the model deployed! Only have the model deployed when needed to minimize costs.

## Outline
* Go to BigQuery and run taxi fare query to understand our data.
* Quickly go through the query and then save the results as a view.
* Open the AutoML Tables UI.
* Import the data and talk through various options for data.
* Once data is imported, talk through the Schema and Analysis tabs.
* Open the training tab and talk through process of training a model.
* Talk through the evaluation metrics and feature importance.
* Show how to serve predictions with your AutoML Tables model.

---

## Script

### Introduction

In this demo we will use AutoML Tables to create a custom regression model without any code. We will do some simple preprocessing on the data via writing a query and then point AutoML to where the preprocessed data lives. AutoML will take over from there, training our model using Neural Architecture Search (NAS) and finding the best model for our data. After our model is trained, it's very simple to evaluate your model's performance and to serve predictions to clients.

### Preprocessing the Dataset

Now for the dataset we will be using in this demo. The NYC Taxi and Limousine Comission public datasets on BigQuery includes trip records from all trips completed in yellow taxis in NYC since 2009. 

Our goal is to build a regression model to predict the fare amount for a given ride. By "fare amount" here, we mean the sum of the base fare and any tolls that a customer would have to pay. In short, we want this amount to represent how much a customer is obliged to pay, so tips will not be included.

Next, what features do we want to use? As you would most likely guess, the time of day and the day of week really affect how much traffic there is. Let's use both the day of the week and the time of the day as two separate features. We will then use the pickup location and dropoff location given in degrees latitude and longitude. Here is our query defining our dataset.

```sql
    SELECT
      (tolls_amount + fare_amount) AS fare_amount,
      EXTRACT(DAYOFWEEK from pickup_datetime) AS dayofweek,
      EXTRACT(HOUR from pickup_datetime) AS hourofday,
      pickup_longitude AS pickuplon,
      pickup_latitude AS pickuplat,
      dropoff_longitude AS dropofflon,
      dropoff_latitude AS dropofflat
    FROM
      `nyc-tlc.yellow.trips`
    WHERE
      trip_distance > 0
      AND fare_amount >= 2.5
      AND pickup_longitude > -78
      AND pickup_longitude < -70
      AND dropoff_longitude > -78
      AND dropoff_longitude < -70
      AND pickup_latitude > 37
      AND pickup_latitude < 45
      AND dropoff_latitude > 37
      AND dropoff_latitude < 45
      AND passenger_count > 0
      AND MOD(ABS(FARM_FINGERPRINT(CAST(pickup_datetime AS STRING))), 5000) = 1
```

Before we move forward, let us take some time and parse our `WHERE` clause. First, NYC yellow cabs have their fare start at \$2.50 the moment you sit down. So any fare amount less than that does not make sense. Likewise, we want to be sure to only count rides that actually occured, so let's be sure the trip distance is nonzero and for similar reasons we will ensure that the passenger count is at least 1. Finally we will filter based on pickup location and dropoff location. In short, we want to be sure that the locations are roughly in the NYC area. 

The last part of the `WHERE` clause may seem a bit weird, but we're using a hashing function on the `pickup_datetime` field and then use that to take 1/5000th of the data. The reason that we're doing this is very simple! The table we're using has around 1.1 billion entries and at least for now we want a more reasonable starting sample size of around 200,000 rows.

Finally for AutoML tables, we need to save our results either in a Google Cloud Storage bucket as a CSV file, or as its own BigQuery table or view. In this case, I'll save the result as a BigQuery view.

We can click on save as view, then put in our project name, dataset name, and I'll name my table `taxi_preprocessed`.

Now we're all set up to use AutoML Tables!

### Introducing AutoML Tables and Uploading Data

AutoML Tables is a tool that allows anyone on your team to automatically build and deploy state-of-the-art machine learning models on stuctured data at massively increased speed and scale. We've done our first step already by preprocessing our data, so let's upload the data to AutoML Tables.

Go to AutoML Tables and click on "New Dataset" at the top of the page.

Since we saved our data in BigQuery, then we just need to point AutoML to it. We select "BigQuery Table or View" and put in our BigQuery project, dataset and view name. Note that we could have imported a CSV file saved in Google Cloud Storage, or even local files as well.

Now we're ready to hit "Import". It will take a few minutes to import the dataset. 

### Preparing to Train

After the dataset is imported, we can see the schema of our data. The columns here should all be familiar; we have fare amount, day of week, hour of day, pickup longitude, pickup latitude, dropoff longitude and dropoff latitude. Notice here it chose a datatype for each column and detects if there are null values. It's always best to double check these. In this case it makes more sense here to treat hour of day as a categorical variable, so let's do that instead.

Also here is where we specify that "fare_amount" is our target, or label. We can also specify how we wish to split our data (we'll use the default 80-10-10 split), a column to weigh specific examples and a timestamp column if relevant.

Before we start to train, we should analyze our dataset. We can see statistics here for every column such as number of distinct values, correlation with the target, and statistics such as the mean and standard deviation for any numeric features. After looking through all of this, now we're ready to train.

### Training out AutoML Tables Model

We click on "Train" to get to the training menu. We enter a number between 1 and 72 for the maximum number of node hours we want to use for training. If we hover over the help button here, we see some recommendations for the amount of training time. For around 200,000 rows it recommends somewhere between 1 and 6 hours. Let's set our budget here for 6 hours. 

A few other options to consider. We can exclude specific columns in the dataset for training, though note the target, weight, and any split columns are automatically excluded. I'll go ahead and keep all 6 of my features here. You can also choose your optimization objective (let's stick to RMSE) and finally change if early stopping is turned on. The idea of early stopping here is if the trials of AutoML are not improving the model after long enough, then it will halt training various models so that you don't waste training time and those additional hours will be refunded.

Once we've done all of this, we hit "Train Model" and just wait! Since this could take up to 6 hours, let us jump over to a model which was already trained on this data.

### Evaluation of Model

Our model has completed its training process, so let's see how it did. We can click on the "Evaluate" tab to look at its performance.

At the top here we see some information about the model. We see a reminder of the target variable, the fact we used 6 feature columns plus the size of our test set (about 22 thousand rows), and that we optimized our model for RMSE (root mean squared error). 

To the right of this information is what we came here for: the RMSE is 3.820. This is a good model with very little effort on our part! We simply gave the preprocessed data to AutoML, specified a few options, and hit "Train". It was that easy.

Note that we can see other metrics for model performance here, such as the RMSLE (root mean squared logarithmic error), MAE (mean absolute error), MAPE (mean absolute percentage error) and Pearson correlation coefficient R^2. Finally if we want to see the predictions on the test set, we can export the predictions to BigQuery. This can be useful if you suspect there's some bias or defect in the model and want to explore these errors more carefully.

Finally below we see the feature importances. We won't go into full detail here, but roughly speaking feature importance is computed by measuring the impact that each feature has on the prediction, when perturbed across a wide spectrum of values sampled from the dataset.  For AutoML Tables, the importances are normalized to sum up to 100% or 1. For those who want more technical details, the feature importance used here is known as "Permutation Feature Importance"

Though taking `timeofday` and `dayofweek` made sense (as a way to capture the amount of traffic), the features derived from the pickup location and dropoff location were significantly more important.

### Prediction with your trained model.

Once our model is trained and we have evaluated our model, then we can predict using our now trained model in a few different ways. We can do batch predictions by uploading data from BigQuery and uploading CSV files from Cloud Storage. We can specify both a BigQuery project or a Cloud Storage bucket for storing our predictions. This is perfect for when you don't need predictions immediately and you're working with accumulated data.

To use online prediction, we need to deploy our model to the cloud. So let's do that...

...Now that it's deployed, let's get a prediction. We can either use the Web UI for one-off examples or make REST API calls. Here we will simply use the Web UI.

In the Web UI, we can put in values for the features we defined before, and simply hit submit...So for this ride from the Google office in the Chelsea neighborhood of Manhattan (Lat 40.740920, Lon -74.002011) to JFK airport's terminal 5 (Lat 40.647085, Lon -73.779942) on a Thursday afternoon at 4:00pm, our model predicts the ride to cost $41.17. Admittedly this prediction seems a little low, but the higher end of the 95% confidence interval seems like it's on the right path. 

As a final note we can generate feature importances for our predictions by checking the box at the bottom "Generate Feature Importance". This will compute the influence each feature value had on the prediction versus a baseline prediction. Baseline values are computed from the training data, using the median value for numeric features and the mode for categorical features. The prediction generated from the baseline values is the baseline prediction score using the SHAP method.














