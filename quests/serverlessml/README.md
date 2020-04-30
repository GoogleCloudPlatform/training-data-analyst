# Serverless Machine Learning with TensorFlow and BigQuery

This one day workshop provides a hands-on introduction to designing and building machine learning models on structured data on Google Cloud Platform. You will learn machine learning (ML) concepts and how to implement them using both BigQuery Machine Learning and TensorFlow/Keras. You will apply the lessons to a large out-of-memory dataset and develop hands-on skills in developing, evaluating, and productionizing ML models.

## Pre-lab setup

__Step 1:__ Create an account at https://events.qwiklabs.com/.

__Step 2:__ Fill out the Labs Signup Form using the link your instructor gives you. Enter the email address of your Qwiklabs account.

__Step 3:__ [Access the Labs and Course PDFs](https://googlecloud.qwiklabs.com/classrooms/in-session)

Tip: Use an __Incognito Window__ for this course to prevent single sign-on issues!

## Audience
- Data Engineers
- Data Scientists
- Data Analysts

## Prerequisties 
- Familiarity with [SQL](https://en.wikipedia.org/wiki/SQL)
- Basic familiarity with [Python](https://en.wikipedia.org/wiki/Python_(programming_language))

## Coursework: Hands-On Labs

Note: If you are an instructor teaching this class via [Qwiklabs](https://www.qwiklabs.com) you can ignore the Pre-work as the student Qwiklabs will automatically create new GCP accounts and walk them through how to clone this repository. 

Each folder in this repository represents one lab and will contain:
  * labs/ <-- partially completed ipynbs with TODOs for you to complete
  * solution/ <-- full solution answers for reference
  
 What follows is a recommended list of labs for this workshop in order:

__Pre-work: [Create a Cloud AI Platform Notebook instance](http://console.cloud.google.com/mlengine/notebooks/create-instance)__
   * Choose TensorFlow 2.0.
   * Choose 2 vCPUs and no GPUs.
   * On the instance, use the Git menu to clone https://github.com/GoogleCloudPlatform/training-data-analyst

__0. [Classify Images of Clouds with AutoML](https://www.qwiklabs.com/focuses/1779?parent=catalog)__ students will use the GCP UI to train multiple image classification models using [AutoML Vision](https://cloud.google.com/vision/automl/docs/) without having to code. 
   * Optional lab - 30 minutes
   * Upload a labeled dataset to Google Cloud Storage and connecting it to AutoML Vision with a CSV label file.
   * Train a model with AutoML Vision and evaluating its accuracy
   * Generate predictions on your trained model

__1. [Explore data](01_explore/) corresponding to taxi rides in New York City__ to build a Machine Learning model in support of a fare-estimation tool.
   * 20-30 minutes
   * Launch a hosted iPython notebook using AI Platform Notebooks
   * Access and explore a public BigQuery dataset on NYC Taxi Cab rides
   * Visualize your dataset using the Seaborn library
   * Inspect and clean-up the dataset for future ML model training
   * Create a benchmark to judge future ML model performance off of

__2. Use BigQuery ML [to build our first ML models](02_bqml/) for taxifare prediction.__
   * 20-30 minutes
   * Train a model on raw data using BigQuery ML in minutes
   * Evalute the forecasting model performance with RMSE
   * Create a second Linear Regression model with cleaned up data
   * Create a third model using a Deep Neural Network (DNN)
   * Evaluate model performance against our initial benchmark

__3. Learn [how to read large datasets](03_tfdata/) using TensorFlow.__
   * 20-30 minutes
   * Use tf.data to read CSV files
   * Load the training data into memory
   * Prune the data by removing columns
   * Use tf.data to map features and labels
   * Adjust the batch size of our dataset
   * Shuffle the dataset to optimize for deep learning

__4. Build a [DNN model](04_keras/) using Keras.__
   * 20-30 minutes
   * Use tf.data to read CSV files
   * Build a simple Keras DNN using its Functional API
   * Train the model using model.fit()
   * Predict with the model using model.predict()
   * Export the model and deploy it to Cloud AI Platform for serving

__5. Improve the basic models through [feature engineering in BQML](05_feateng/)__
   * 20-30 minutes
   * Apply transformations using SQL to prune the taxi cab dataset
   * Create and train a new Linear Regression model with BigQuery ML
   * Evaluate and predict with the linear model
   * Create a feature cross for day-hour combination using SQL
   * Examine ways to reduce model overfitting with regularization
   * Create and train a DNN model with BigQuery ML

__6. Carry out equivalent [feature engineering in Keras](06_feateng_keras/)__
   * 20-30 minutes
   * Use tf.data to read the CSV files
   * Apply feature engineering techniques to transform the input data
   * Create new feature columns for better predictive power
   * Build, train, and evaluate a new Keras DNN
   * Make example predictions
   * Export the model in preparation for serving later

__7. [Productionize the models](07_caip/)__
   * 20-30 minutes
   * Export training code from a Keras notebook into a trainer file
   * Create a Docker container based on a DLVM container
   * Deploy a training job to a cluster on Cloud AI Platform
   * Export [larger dataset](07_caip/solution/export_data.ipynb)
   * OPTIONAL: Train Keras model by [submitting notebook](07_caip/solution/run_notebook.sh)
   * Train [using container](07_caip/solution/train_caip.ipynb) on Cloud AI Platform Training


   
## Instructor Guide
### Troubleshooting tips
Here are some known issues:
   * On Qwiklabs, they should not hit End Lab until the end of the day.
   * On Qwiklabs, links in notebooks to BigQuery tables and datasets sometimes take the user to the wrong Google account (where the dataset/table in question is not visible). A quick workaround in those situations is to navigate to BigQuery from the Google Cloud Console instead.
   * Note that a valid region name is ```us-west1```. A string such as ```us-west1-b``` is a zone. Many gcloud commands will fail with resource unavailable errors if you pass in a zone where the notebook asks for a ```REGION```

### Timing guide
   * 9.15am start
   * 10am to 10.30am Lab 1
   * 11am to 11.30am Lab 2
   * 11.55am to 12.30pm Lab 3
   * 12.30pm to 1.00pm Lunch
   * 1.45pm to 2.15pm Lab 4
   * 2.45pm to 3.15pm Lab 5
   * 3.30pm to 4.00pm Lab 6
   * 4.15pm to 4.30pm Lab 7
   * 4.45pm end
 
