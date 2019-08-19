## Serverless Machine Learning with TensorFlow and BigQuery

This workshop provides a hands-on introduction to designing and building machine learning models on structured data on Google Cloud Platform. You will learn machine learning (ML) concepts and how to implement them using both BigQuery Machine Learning and TensorFlow/Keras. You will apply the lessons to a large out-of-memory dataset and develop hands-on skills in developing, evaluating, and productionizing ML models.

1. [Explore data](01_explore/explore_data.ipynb) corresponding to taxi rides in New York City to build a Machine Learning model in support of a fare-estimation tool.
2. Use BigQuery ML [to build our first ML models](02_bqml/first_model.ipynb) for taxifare prediction.
3. Learn [how to read large datasets](03_tfdata/input_pipeline.ipynb) using TensorFlow.
4. Build a [DNN model](04_keras/keras_dnn.ipynb) using Keras.
5. Improve the basic models through [feature engineering in BQML](05_feateng/feateng_bqml.ipynb)
6. Carry out equivalent [feature engineering in Keras](06_feateng_keras/taxifare_fc.ipynb)
7. Productionize the models
   * Export [larger dataset](07_caip/export_data.ipynb)
   * Train Keras model by [submitting notebook](07_caip/run_notebook.sh)
   * Train [using container](07_caip/train_caip.ipynb) on Cloud AI Platform Training

