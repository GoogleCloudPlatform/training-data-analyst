The sample pipelines give you a quick start to build and deploy machine learning pipelines with Kubeflow Pipeline.
* Follow the guide to [deploy the Kubeflow pipelines service](https://www.kubeflow.org/docs/guides/pipelines/deploy-pipelines-service/).
* Build and deploy your pipeline [using the provided samples](https://www.kubeflow.org/docs/guides/pipelines/pipelines-samples/).

# Sample Structure
The samples are organized into the core set and the contrib set. 

**Core samples** demonstrates the full KFP functionalities and are covered by the sample test infra. 
The current status is not all samples are covered by the tests but they will be all covered in the near future.
A selected set of these core samples will also be preloaded to the KFP during deployment. 
The core samples will also include intermediate samples that are 
more complex than basic samples such as flip coins but simpler than TFX samples. 
It serves to demonstrate a set of the outstanding features and offers users the next level KFP experience.

**Contrib samples** are not tested by KFP and could potentially be moved to
the core samples if the samples are of good qualty and tests are covered and it demonstrates certain KFP functionality. 
Another reason to put some samples in this directory is that some samples require certain 
platform support that is hard to support in our test infra.

In the Core directory, each sample will be in a separate directory. 
In the Contrib directory, there is an intermediate directory for each contributor, 
e.g. ibm and arena, within which each sample is in a separate directory. 
An example of the resulting structure is as follows: 
```
pipelines/samples/
Core/
	dsl_static_type_checking/
		dsl_static_type_checking.ipynb
	xgboost_training_cm/
		xgboost_training_cm.py
	condition/
		condition.py
	recursion/
		recursion.py
Contrib/
	IBM/
		ffdl-seldon/
			ffdl_pipeline.ipynb
			ffdl_pipeline.py
			README.md
```

# Run Samples

## Compile the pipeline specification

Follow the guide to [building a pipeline](https://www.kubeflow.org/docs/guides/pipelines/build-pipeline/) to install the Kubeflow 
Pipelines SDK and compile the sample Python into a workflow specification. 
The specification takes one of the three forms: YAML file, YAML compressed into a `.tar.gz` file, and YAML compressed into a `.zip` file

For convenience, you can use the preloaded samples in the pipeline system. This saves you the steps required
to compile and compress the pipeline specification.

## Upload the pipeline to the Kubeflow Pipeline

Open the Kubeflow pipelines UI, and follow the prompts to create a new pipeline and upload the generated workflow
specification, `my-pipeline.zip` (example: `sequential.zip`).

## Run the pipeline

Follow the pipeline UI to create pipeline runs. 

Useful parameter values:

* For the "exit_handler" and "sequential" samples: `gs://ml-pipeline-playground/shakespeare1.txt`
* For the "parallel_join" sample: `gs://ml-pipeline-playground/shakespeare1.txt` and `gs://ml-pipeline-playground/shakespeare2.txt`

## Notes: component source codes

All samples use pre-built components. The command to run for each container is built into the pipeline file.

# Sample contribution
For better readability and integrations with the sample test infrastructure, samples are encouraged to adopt the following conventions.

* The sample file should be either `*.py` or `*.ipynb`, and its file name is consistent with its directory name.
* For `*.py` sample, it's recommended to have a main invoking `kfp.compiler.Compiler().compile()` to compile the 
pipeline function into pipeline yaml spec.
* For `*.ipynb` sample, parameters (e.g., `project_name`)
should be defined in a dedicated cell and tagged as parameter. 
(If the author would like the sample test infra to run it by setting the `run_pipeline` flag to True in 
the associated `config.yaml` file, the sample test infra will expect the sample to use the
`kfp.Client().create_run_from_pipeline_func` method for starting the run so that the sample test can watch the run.)
Detailed guideline is 
[here](https://github.com/nteract/papermill). Also, all the environment setup and 
preparation should be within the notebook, such as by `!pip install packages` 


## How to add a sample test
Here are the ordered steps to add the sample tests for samples. 
Only the core samples are expected to be added to the sample test infrastructure.

1. Make sure the sample follows the [sample conventions](#sample-contribution).
2. If the sample requires argument inputs, they can be specified in a config yaml file
placed under `test/sample-test/configs`. See 
[`xgboost_training_cm.config.yaml`](https://github.com/kubeflow/pipelines/blob/master/test/sample-test/configs/xgboost_training_cm.config.yaml) 
as an example. 
The config yaml file will be validated according to `schema.config.yaml`. 
If no config yaml is provided, pipeline parameters will be substituted by their default values.
3. Add your test name (in consistency with the file name and dir name) in 
[`test/sample_test.yaml`](https://github.com/kubeflow/pipelines/blob/ecd93a50564652553260f8008c9a2d75ab907971/test/sample_test.yaml#L69)
4. (*Optional*) The current sample test infra only checks if runs succeed without custom validation logic. 
If needed, runtime checks should be included in the sample itself. However, there is no custom validation logic 
injection support for `*.py` samples, in which case the test infra compiles the sample, submit and run the sample, and check if it succeeds.
