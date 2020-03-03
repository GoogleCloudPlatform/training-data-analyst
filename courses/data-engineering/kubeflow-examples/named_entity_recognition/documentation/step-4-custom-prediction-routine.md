# Custom prediction routine

Custom prediction routines allow us to specify additional code that runs with every prediction request.
Without custom prediction routine the machine learning framework handles the prediction operation.

## Why custom prediction routine
Our model requires numeric inputs, which we convert from text before training (this is the preprocessing step). To perform the same conversion at prediction time, inject the preprocessing code by defining a custom prediction routine.

> Without a custom prediction routine, you would need to create a wrapper, e.g. with App Engine or Cloud Functions, which would add complexity and latency.

## How do custom prediction routines work?

Our custom prediction routine requires six parts

* `keras_saved_model.h5` - The model stored as part of our training component (artifact).
* `processor_state.pkl` - The preprocessing state stored as part of our training component (artifact).
* `model_prediction.py` - The custom prediction routine logic.
* `text_preprocessor.py` - The pre-processing logic.  
* `custom_prediction_routine.tar.gz` - A Python package `tar.gz` which contains our implementation.
* `setup.py` - Used to create the Python package. 

To build our custom prediction routine run the build script located `/routine/build_routine.sh`. This creates a `tar.gz` which is required when you deploy your model. 

Navigate to the routine folder `/routine/` and run the following build script:

```bash
$ ./build_routine.sh
```

## Upload custom prediction routine to Google Cloud Storage

```bash
gsutil cp custom_prediction_routine-0.2.tar.gz gs://${BUCKET}/routine/custom_prediction_routine-0.2.tar.gz
```

*Next*: [Run the pipeline](step-5-run-pipeline.md)

*Previous*: [Upload the dataset](step-3-upload-dataset.md)