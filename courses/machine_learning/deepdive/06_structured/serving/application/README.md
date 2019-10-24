# Baby Weight Prediction Example

Disclaimer: This is not an official Google product.

This is an example application demonstrating how the deployed model
 can be used to make online predictions from web applications.

## Start Cloud AI Platform Notebook instance
* Start AI Platform Notebooks
* git clone this repository

## Train, export, deploy the model
* Open 3_keras_dnn.ipynb
* Modify PROJECT, BUCKET, REGION
* Run the notebook

## Customize the model name
If you have deployed the model with the name different from 'babyweight',
 open `app.yaml` with a text editor and replace the model name accordingly.

```yaml
env_variables:
  MODEL_NAME: 'babyweight'
  VERSION_NAME: 'dnn'
```

## Deploy the AppEngine application
* In CloudShell, git clone this repository
```shell
$ pip install --user -r requirements.txt -t lib
$ gcloud app create
$ gcloud app deploy
```

By executing these commands on the Cloud Shell, the project id is automatically
 applied to the application and the application URL will be
 `https://[project id].appspot.com`.

Now you can access the URL from your browser to use the web application
 to predict a baby's weight.
 
 ![](docs/img/screenshot.png) 
