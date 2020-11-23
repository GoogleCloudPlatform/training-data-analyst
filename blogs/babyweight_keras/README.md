# Structured data prediction using Cloud AI Platform

*Disclaimer: This is not an official Google product.*

This is an example notebook to explain how you can create a Keras model using the feature columns, and train it on Cloud AI Platform.

## Setup

1. Create a new GCP project and enable the following API. 
- AI Platform Training & Prediction API
- Notebooks API
- Dataflow API

2. Launch a new notebook instance from the "AI Platform -> Notebooks" menu. Choose "TensorFlow Enterprise 2.3 without GPUs" for the instance type.

3. Open JupyterLab and execute the following commond from the JupyterLab terminal.

```
git clone https://github.com/GoogleCloudPlatform/training-data-analyst.git
```

4. Open the notebook `training-data-analyst/blogs/babyweight_keras/babyweight.ipynb` and follow the instruction.
