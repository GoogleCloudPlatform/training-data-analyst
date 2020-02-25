# Poetry Prediction Service

Disclaimer: This is not an official Google product.

This is an example application demonstrating how to deploy a T2T application as a service

## Products
- [Cloud Machine Learning Engine][1]
- [App Engine][2]

## Language
- [Python][3]

[1]: https://cloud.google.com/ml-engine/
[2]: https://cloud.google.com/appengine/docs
[3]: https://python.org

## Prerequisites
You are supposed to have deployed the trained model for online predictions
 by following the instruction in the Cloud Datalab [notebook][4]. You need to
 use the same project to run this application.

[4]: https://github.com/GoogleCloudPlatform/training-data-analyst/blob/master/courses/machine_learning/deepdive/poetry.ipynb

## Do this first
In this section you will start your [Google Cloud Shell][6] and clone the
 application code repository to it.

1. [Open the Cloud Console][7]

2. Click the Google Cloud Shell icon in the top-right and wait for your shell
 to open:

 ![](docs/img/cloud-shell.png)

3. Clone the lab repository in your cloud shell, then `cd` into that dir:

  ```shell
  $ git clone https://github.com/GoogleCloudPlatform/training-data-analyst
  Cloning into 'training-data-analyst'...
  ...

  $ cd training-data-analyst/
  ```

[6]: https://cloud.google.com/cloud-shell/docs/
[7]: https://console.cloud.google.com/

## Customize the model name

If you have deployed the model with the name different from 'poetry',
 open `app.yaml` with a text editor and replace the model name accordingly.

```yaml
env_variables:
  MODEL_NAME: 'poetry'
```

## Deploy the application

```shell
$ pip install -r requirements.txt -t lib
$ gcloud app create
$ gcloud app deploy
```

By executing these commands on the Cloud Shell, the project id is automatically
 applied to the application and the application URL will be
 `https://[project id].appspot.com`.

Now you can access the URL from your browser to use the web application
 
 ![](docs/img/screenshot.png) 
