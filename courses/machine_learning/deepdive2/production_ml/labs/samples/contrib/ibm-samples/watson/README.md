The `Watson Train and Serve` sample pipeline runs training, storing and deploying a Tensorflow model with MNIST handwriting recognition using [IBM Watson Studio](https://www.ibm.com/cloud/watson-studio) and [IBM Watson Machine Learning](https://www.ibm.com/cloud/machine-learning) service.

# Requirements

This sample requires the user to have provisioned a machine learning service on Watson, a cloud object store set up and the service credentials configured in the creds.ini file.

To provision your own Watson Machine Learning services and cloud object store, following are the required steps.

* IBM Watson Machine Learning service instance

To create a machine learning service, go to [IBM Cloud](https://console.bluemix.net), login with IBM account id first. From the `Catalog` page, click on `AI` tab on the left side to go to this [page](https://console.bluemix.net/catalog/?category=ai). Then click on the [`Machine Learning`](https://console.bluemix.net/catalog/services/machine-learning) link and follow the instructions to create the service.

Once the service is created, from service's `Dashboard`, follow the instruction to generate `service credentials`. Refer to IBM Cloud [documents](https://console.bluemix.net/docs/) for help if needed. Collect the `url`, `apikey`, and `instance_id` info from the service credentials as these will be required to access the service.

* A cloud object store

Watson Machine Learning service loads datasets from cloud object store and stores model outputs and other artifacts to cloud object store. Users can use any cloud object store they already preserve. Users can also create a cloud object store with `IBM Cloud Object Storage` service by following this [link](https://console.bluemix.net/catalog/services/cloud-object-storage).

Collect the `access_key_id` and `secret_access_key` fields from the service credentials for the cloud object store. Create the service credentials first if not existed. To ensure generating HMAC credentials, specify the following in the `Add Inline Configuration Parameters` field: `{"HMAC":true}`.  

Collect the `endpoint` info from the endpoint section in the cloud object store service.

Create two buckets, one for storing the train datasets and model source codes, and one for storing the model outputs.

* Set up access credentials

This pipeline sample reads the credentials from a file hosted in a github repo. Refer to `creds.ini` file and input user's specific credentials. Then upload the file to a github repo the user has access.

Note: make sure the `cos_endpoint` value in the `creds.ini` file must have at least a scheme and hostname.

To access the credentials file, the user should provide a github access token and the link to the raw content of the file. Modify the `GITHUB_TOKEN` and `CONFIG_FILE_URL` variables in the `watson_train_serve_pipeline.py` file with the user's access token and link.

# The datasets

This pipeline sample uses the [MNIST](http://yann.lecun.com/exdb/mnist) datasets, including [train-images-idx3-ubyte.gz](http://yann.lecun.com/exdb/mnist/train-images-idx3-ubyte.gz), [train-labels-idx1-ubyte.gz](http://yann.lecun.com/exdb/mnist/train-labels-idx1-ubyte.gz), [t10k-images-idx3-ubyte.gz](http://yann.lecun.com/exdb/mnist/t10k-images-idx3-ubyte.gz), and [t10k-labels-idx1-ubyte.gz](http://yann.lecun.com/exdb/mnist/t10k-labels-idx1-ubyte.gz).

If users are using their own cloud object store instances, download these datasets and upload to the input bucket created above on the cloud object store.

# Upload model code and datasets

Once the user has the model train source code ready, compress all files into one `zip` format file.

For example, run following command to compress the sample model train codes

```command line
pushd source/model-source-code
zip -j tf-model tf-model/convolutional_network.py tf-model/input_data.py
popd
```

This should create a `tf-model.zip` file.

Upload the model train code, together with the train datasets, to the input bucket created above in the cloud object store.

# Upload model scoring payload

At the end of the deploy stage of this sample, `tf-mnist-test-payload.json` is used as the scoring payload to test the deployment. Upload this file to the input bucket in the cloud object store.

# Compling the pipeline template

First, install the necessary Python package for setting up the access to the Watson Machine Learning service and cloud object store, with following command

```command line
pip3 install ai_pipeline_params
```

Then follow the guide to [building a pipeline](https://www.kubeflow.org/docs/pipelines/build-pipeline/) to install the Kubeflow Pipelines SDK, and run the following command to compile the sample `watson_train_serve_pipeline.py` file into a workflow specification.

```
dsl-compile --py watson_train_serve_pipeline.py --output wml-pipeline.tar.gz
```

Then, submit `wml-pipeline.tar.gz` to the kubeflow pipeline UI. From there you can create different experiments and runs using the Watson pipeline definition.
