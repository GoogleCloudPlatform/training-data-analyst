# Overview
[Tensorflow Extended (TFX)](https://github.com/tensorflow/tfx) is a Google-production-scale machine
learning platform based on TensorFlow. It provides a configuration framework to express ML pipelines
consisting of TFX components. Kubeflow Pipelines can be used as the orchestrator supporting the 
execution of a TFX pipeline.

This directory contains a sample that demonstrate how to author a ML pipeline 
to solve the famous [iris flower classification problem](https://www.kaggle.com/arshid/iris-flower-dataset) 
in TFX and run it on a KFP deployment. Specifically it highlights the following
functionalities:

1. Support of [Keras](https://keras.io/) API;
2. Use [TFMA](https://github.com/tensorflow/model-analysis) for model validation;
3. Warm-start training by Resolver.

# Compilation
In order to successfully compile the Python sample, it is recommended to use
`tfx>=0.21.2`.

# Permission

> :warning: If you are using **full-scope** or **workload identity enabled** cluster in hosted pipeline beta version, **DO NOT** follow this section. However you'll still need to enable corresponding GCP API.

This pipeline requires Google Cloud Storage permission to run. 
If KFP was deployed through K8S marketplace, please follow instructions in 
[the guideline](https://github.com/kubeflow/pipelines/blob/master/manifests/gcp_marketplace/guide.md#gcp-service-account-credentials)
to make sure the service account has `storage.admin` role.
If KFP was deployed through 
[standalone deployment](https://github.com/kubeflow/pipelines/tree/master/manifests/kustomize) 
please refer to [Authenticating Pipelines to GCP](https://www.kubeflow.org/docs/gke/authentication-pipelines/)
to provide `storage.admin` permission.