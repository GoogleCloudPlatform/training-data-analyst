# tf_encoder_decoder_autoencoder_anomaly_detection

This project is an encoder-decoder autoencoder machine learning model to perform anomaly detection on time-series data such as IoT sensor data or cybersecurity data.

This is mostly an implementation of this research paper: [LSTM-based Encoder-Decoder for Multi-sensor Anomaly Detection](https://arxiv.org/pdf/1607.00148.pdf).

## lstm_encoder_decoder_autoencoder_anomaly_detection_local
This notebook is a local implementation of the model that contains a data generator for creating data as well as the TensorFlow model and Estimator. 

### Data generator
The current data generator creates different sinusoids for both normal and anomalous sequences. This can be replaced with any other time series data that you want to perform anomaly detection on as long as it matches the correct input format. The format is a delimited string that separates features and internal to each feature the timesteps are delimited by a different separator.

For example for data that contains three features and five timesteps where the first subscript is feature index and the second subscript is timestep index, a row of input data would look like the following:
x00,x01,x02,x03,x04;x10,x11,x12,x13,x14;x20,x21,x22,x23,x24

This data is then read into the input function, batched, and sent to the custom model function.

### Model function
This model function has several subgraphs that are called based on a combination of the mode and hyperparameters passed into it.

#### Reconstruction, train and evaluate
We first instantiate our custom estimator with the evaluation_mode hyperparameter set to "reconstruction". This is then sent to train_and_evaluate where two different subgraphs are run for training and evaluation.

##### mode == TRAIN
During training we will train the encoder-decoder weight parameters. Our features will be the input time series data and since it is an autoencoder our labels will be our inputs. Our predictions will be the reconstructed inputs that we aim, through gradient descent, to be as close to the inputs as possible using a mean squared error loss. This trains on the normal sequence training dataset.

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