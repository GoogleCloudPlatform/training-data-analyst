
# Kubeflow Pipelines - GitHub Issue Summarization

This Kubeflow Pipelines example shows how to build a web app that summarizes GitHub issues using Kubeflow Pipelines to train and serve a model.
The pipeline trains a [Tensor2Tensor](https://github.com/tensorflow/tensor2tensor/) model on GitHub issue data, learning to predict issue titles from issue bodies. It then exports the trained model and deploys the exported model using  [Tensorflow Serving](https://github.com/tensorflow/serving). The final step in the pipeline launches a web app, which interacts with the TF-Serving instance in order to get model predictions.

You can follow this example as a codelab: [g.co/codelabs/kfp-gis](https://g.co/codelabs/kfp-gis).

<!-- Or, you can run it as a [Cloud shell Tutorial](https://console.cloud.google.com/?cloudshell=true&cloudshell_git_repo=https://github.com/kubeflow/examples&working_dir=github_issue_summarization/pipelines&cloudshell_tutorial=tutorial.md).  The source for the Cloud Shell tutorial is [here](tutorial.md). -->

