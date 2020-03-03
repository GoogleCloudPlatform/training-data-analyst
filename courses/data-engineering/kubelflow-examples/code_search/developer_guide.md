# Developer guide for the code search example

This doc is intended for folks looking to contribute to the example.

## Testing

We currently have tests that can be run manually to test the code. 
We hope to get these integrated into our CI system soon.

### T2T Test

The test code_search/src/code_search/t2t/similarity_transformer_test.py
can be used to test 

   * Training
   * Evaluation
   * Model Export

The test can be run as follows

```
cd code_search/src
python3 -m code_search.t2t.similarity_transformer_test
```
The test just runs the relevant T2T steps and verifies they succeeds. No additional
checks are executed.


### TF Serving test

code_search/src/code_search/nmslib/cli/embed_query_test.py


Can be used to test generating predictions using TFServing.

The test assumes the TFServing is running in a docker container

You can start TFServing as follows

```
./code_search/nmslib/cli/start_test_server.sh 
```

You can then run the test

```
export PYTHONPATH=${EXAMPLES_REPO/code_search/src:${PYTHONPATH}
python3 -m embed_query_test
```

The test verifies that the code can successfully generate embeddings using TFServing.

The test verifies that different embeddings are computed for the query and the code.

**start_test_server.sh** relies on a model stored in **code_search/src/code_search/t2t/**
A new model can be produced by running **similarity_transformer_export_test**. The unittest
will export the model to a temporary directory. You can then copy that model to the test_data
directory.