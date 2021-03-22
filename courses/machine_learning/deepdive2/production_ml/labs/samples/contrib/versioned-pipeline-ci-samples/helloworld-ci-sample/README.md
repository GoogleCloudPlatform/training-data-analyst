# Hello World CI Sample

## Overview

This sample uses cloudbuild to implement the continuous integration process of a simple pipeline that outputs "hello world" to the console. Once all set up, you can push your code to github repo, then the build process in cloud build will be triggered automatically, then a run will be created in kubeflow pipeline. You can view your pipeline and the run in kubeflow pipelines. 

Besides, we use **REST API** to call kubeflow pipeline to create a new version and a run in this sample. Other methods to create pipeline version can be found in mnist sample in this repo, i.e., use Kubeflow Pipeline SDK.

## Usage

To use this pipeline, you need to:

* Set up a trigger in cloud build that connects to your github repo.
* Replace the constants to your own configuration in cloudbuild.yaml
* Replace images in the pipeline.py to your own images (the ones you built in cloudbuild.yaml)
* Set your cloud registry public accessible
* Set your bucket public accessible, or authenticate cloudbuild to cloud storage