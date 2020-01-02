Background Processing
---------------------

This directory contains an example of doing background processing with App
Engine, Cloud Pub/Sub, Cloud Functions, and Firestore.

Deploy commands:

From the app directory:
```
$ gcloud app deploy
```

From the function directory, after creating the PubSub topic:
```
$ gcloud functions deploy --runtime=python37 --trigger-topic=translate Translate --set-env-vars GOOGLE_CLOUD_PROJECT=my-project
```
