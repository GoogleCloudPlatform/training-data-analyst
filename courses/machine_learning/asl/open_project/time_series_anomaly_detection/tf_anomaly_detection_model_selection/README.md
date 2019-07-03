# tf_anomaly_detection_model_selection

This project is a PCA machine learning model to perform anomaly detection on time-series data such as IoT sensor data or cybersecurity data.

## model_selection_anomaly_detection_local
This notebook is a local implementation of the model that contains a data generator for creating data as well as the TensorFlow model and Estimator. 

### Data generator
The current data generator creates different sinusoids for both normal and anomalous sequences. This can be replaced with any other time series data that you want to perform anomaly detection on as long as it matches the correct input format. The format is a delimited string that separates features and internal to each feature the timesteps are delimited by a different separator.

For example for data that contains three features and five timesteps where the first subscript is feature index and the second subscript is timestep index, a row of input data would look like the following:
x00;x01;x02;x03;x04,x10;x11;x12;x13;x14,x20;x21;x22;x23;x24

This data is then read into the input function, batched, and sent to the custom model function.

### Model function
This model function has several subgraphs that are called based on a combination of the mode and hyperparameters passed into it. There is the option to use multiple different model types: dense_autoencoder, lstm_encoder_decoder_autoencoder, and pca.

#### Reconstruction, train and evaluate
We first instantiate our custom estimator with the evaluation_mode hyperparameter set to "reconstruction". This is then sent to train_and_evaluate where two different subgraphs are run for training and evaluation.

##### mode == TRAIN
During training we will train the model parameters over batches of data. Our features will be the input time series data and since it is an autoencoder our labels will be our inputs. Our predictions will be the reconstructed inputs that we aim, to be as close to the inputs as possible using a mean squared error loss. This trains on the normal sequence training dataset.

##### mode == EVAL
During evaluation, we will calculate the RMSE and MAE of the reconstruction error. This evaluates on the normal sequence validation dataset and has an early stopping hook.

#### Calculate error distribution statistics, train
We next have to calculate the error distribution statistics, specifically the mean and covariance for maximum likelihood estimation which will be later used to calculate the Mahalanobis distance. These are saved in variables which are separate from the reconstruction encoder-decoder variables. A new checkpoint needs to be written with these values, therefore we reinstantiate the estimator but this time with evaluation_mode hyperparameter set to "calculate_error_distribution_statistics" to use that subgraph and then train that estimator. It will load in the saved encoder-decoder reconstruction variables and perform running updates across batches for the reconstruction error MLE variables.

##### mode == TRAIN
Calculates the absolute error of reconstruction and then calculates the count, mean, covariance, and inverse covariance for both the time and features dimension. There is methods to cover the case of singleton and batch updates.

#### Tune anomaly thresholds, eval
The anomaly thresholds for both timesteps and features can either be set manually or automatically. If a point's Mahalanobis distance is above this value then the point will be flagged anomalous, otherwise it will be flagged normal.

##### mode == EVAL
To tune the anomaly thresholds, we will try many different thresholds for each time based and feature based views of the error distribution. The thresholds will be chosen based on which ever produces the maximal F-beta score for each respectively.

## model_selection_anomaly_detection_gcp
This notebook is a Google Cloud Platform implementation of the model that uses data files created from above data generator stored in a GCS bucket.

### Create python module
Create a model.py and task.py file to hold all of the model and command line parsing code.

### Run python module locally.
Now we will call python to locally run each of the training phases. Due to running on GCP, the custom estimator will now always use tf.estimator.train_and_evaluate which uses in the train_spec max_steps which we will have to manually calculate for training phases 2 and 3. We want just one epoch worth of training therefore the number of steps will be len(dataset) / batch_size.

#### Reconstruction, train_and_evaluate
This will run the module through the reconstruction phase. Here you do NOT want to run through your training dataset only once, therefore max_steps_reconstruction = len(training_dataset) * num_epochs / batch_size.

#### Calculate error distribution statistics, train_and_evaluate
This will run the module through the error distribution statistics calculation phase. Here you want to run through your unlabeled validation dataset only once, but since it is max_steps you need to add the number of steps you already trained in the previous stage, therefore max_steps_error_distribution = max_steps_reconstruction + len(unlabeled_validation_dataset) / batch_size.

#### Tune anomaly thresholds, train_and_evaluate
This will run the module through the anomaly threshold tuning phase. Here you want to run through your labeled validation dataset only once, but since it is max_steps you need to add the number of steps you already trained in the previous stages, therefore max_steps_tune_anomaly_thresholds = max_steps_error_distribution + len(labeled_validation_dataset) / batch_size.

### Train and hyperparameter tune on Google Cloud
If those local runs completed successfully then we can move to training on GCP each of the three phases and hyperparameter tuning the first phase's hyperparameters.

### Deploy model
Once everything has been trained we can now deploy our exported model.

### Prediction
When the model is deployed we will now interact with our serving input function to create predictions. We first do this locally and then through the deployed model for each normal sequences and anomalous sequences from our test dataset.