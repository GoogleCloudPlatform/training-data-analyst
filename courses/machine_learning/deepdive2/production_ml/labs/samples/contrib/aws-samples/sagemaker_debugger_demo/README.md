# Sample Pipeline for Training Component with Debugger

The `sagemaker-debugger-demo.py` sample creates a pipeline consisting of only a training component. In that component we are using the XGBoost algorithm but with poor hyperparameter choices. By enabling debugger rules and hooks, we can quickly learn that the model produced has issues.

## Prerequisites

This pipeline uses the exact same setup as [simple_training_pipeline](https://github.com/kubeflow/pipelines/tree/master/samples/contrib/aws-samples/simple_train_pipeline). For the purposes of this demonstration, all resources will be created in the `us-east-1` region.

## Steps
1. Compile the pipeline:
   `dsl-compile --py debugger-training-pipeline.py --output debugger-training-pipeline.tar.gz`
2. In the Kubeflow UI, upload this compiled pipeline specification (the .tar.gz file), fill in the necessary run parameters, and click create run.
3. Once the pipeline has finished running, you can view the results of each debugger rule under 'Logs'.

Inputs format to `debug_hook_config` and `debug_rule_config` :
```buildoutcfg
debug_hook_config = {
    "S3OutputPath": "s3://<your_bucket_name>/path/for/data/emission/",
    "LocalPath": "/local/path/for/data/emission/",
    "CollectionConfigurations": [
        {
          "CollectionName": "losses",
          "CollectionParameters": {
            "start_step": "25",
            "end_step": "150"
          }
        }, {
            "CollectionName": "gradient",
            "CollectionParameters": {
                "start_step": "5",
                "end_step": "100"
            }
        }
    ],
    "HookParameters": {
        "save_interval": "10"
    }
}

debug_rule_config = {
    "RuleConfigurationName": "rule_name"
    "RuleEvaluatorImage": "503895931360.dkr.ecr.us-east-1.amazonaws.com/sagemaker-debugger-rules:latest"
    "RuleParameters": {
        "rule_to_invoke": "VanishingGradient",
        "threshold": "0.01"
    }
}
```

# Resources
* [Amazon SageMaker Debugger](https://docs.aws.amazon.com/sagemaker/latest/dg/train-debugger.html)
* [Available Frameworks to Use Debugger](https://docs.aws.amazon.com/sagemaker/latest/dg/train-debugger.html#debugger-supported-aws-containers)
* [Debugger Built-In Rules](https://docs.aws.amazon.com/sagemaker/latest/dg/debugger-built-in-rules.html)
* [Debugger Custom Rules](https://docs.aws.amazon.com/sagemaker/latest/dg/debugger-custom-rules.html)
* [Debugger API Examples](https://docs.aws.amazon.com/sagemaker/latest/dg/debugger-createtrainingjob-api.html)

