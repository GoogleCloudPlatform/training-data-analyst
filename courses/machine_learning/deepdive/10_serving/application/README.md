## Prerequisites
A deployed babyweight model

## Deploy the AppEngine web application

```shell
$ pip install -r requirements.txt -t lib
$ gcloud app create
$ gcloud app deploy
```

By executing these commands on the Cloud Shell, the project id is automatically
 applied to the application and the application URL will be
 `https://[project id].appspot.com`.

Now you can access the URL from your browser to use the web application
 to predict a baby's weight.
 
 ![](docs/img/screenshot.png) 
