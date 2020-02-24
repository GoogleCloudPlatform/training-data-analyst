## How to deploy interpretable models on Google Cloud Platform

[Explainable AI](https://cloud.google.com/explainable-ai) refers to the collection of methods and techniques which enable a human to understand why a model is giving specific results. This can be done in Google Cloud with the following steps:

1. Train a model and deploy it on GCP.
2. Upload a JSON file that contains baseline feature values to a Cloud Storage Bucket.
3. Create a version of the model using this JSON file and specifying the `explanation-method`.
4. Call `gcloud beta ai-platform explain` to get the explanations.

The detailed steps are found in the above [notebook](./AI_Explanations_on_CAIP.ipynb) or in a [Colab notebook](https://colab.research.google.com/drive/1i3xQO5XMGFPrCyP0YQ5JdIlZUMpzpt-q).
