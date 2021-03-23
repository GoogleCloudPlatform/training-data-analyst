# Overview
[Tensorflow Extended (TFX)](https://github.com/tensorflow/tfx) is a Google-production-scale machine
learning platform based on TensorFlow. It provides a configuration framework to express ML pipelines
consisting of TFX components. Kubeflow Pipelines can be used as the orchestrator supporting the 
execution of a TFX pipeline.

This directory contains two samples that demonstrate how to author a ML pipeline in TFX and run it 
on a KFP deployment. 
* `parameterized_tfx_oss.py` is a Python script that outputs a compiled KFP workflow, which you can
  submit to a KFP deployment to run;
* `parameterized_tfx_oss.ipynb` is a notebook version of `parameterized_tfx_oss.py`, and it also
  includes the guidance to setup its dependencies.

Please refer to inline comments for the purpose of each step in both samples.

# Compilation
* `parameterized_tfx_oss.py`: 
In order to successfully compile the Python sample, you'll need to have a TFX installation at 
version 0.21.2 by running `python3 -m pip install tfx==0.21.2`. After that, under the sample dir run
`python3 parameterized_tfx_oss.py` to compile the TFX pipeline into KFP pipeline package.
The compilation is done by invoking `kfp_runner.run(pipeline)` in the script.

* `parameterized_tfx_oss.ipynb`:
The notebook sample includes the installation of various dependencies as its first step.

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

# Execution
* `parameterized_tfx_oss.py`:
You can submit the compiled package to a KFP deployment and run it from the UI.

* `parameterized_tfx_oss.ipynb`:
The last step of the notebook the execution of the pipeline is invoked via KFP SDK client. Also you
have the option to submit and run from UI manually.

### Known issues
* This approach only works for string-typed quantities. For example, you cannot parameterize 
`num_steps` of `Trainer` in this way.
* Name of parameters should be unique.
* By default pipeline root is always parameterized with the name `pipeline-root`.
* If the parameter is referenced at multiple places, the user should
make sure that it is correctly converted to the string-formatted placeholder by
calling `str(your_param)`.
* The best practice is to specify TFX pipeline root to an empty dir. In this sample Argo 
automatically do that by plugging in the 
workflow unique ID (represented `kfp.dsl.RUN_ID_PLACEHOLDER`) to the pipeline root path.
