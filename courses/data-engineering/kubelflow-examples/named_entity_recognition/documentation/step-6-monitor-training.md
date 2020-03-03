# Monitor your pipeline

## Pipeline steps
Open Kubeflow and go to `pipeline dashboard` click `experiments` and open the `run`. You can see the pipeline graph which shows each step in our pipeline. As you can see all of your steps completed successfully.

![monitor pipeline](files/monitor-pipeline.png)


## Open TensorBoard
During the training of your model, you are interested how your model loss and accuracy changes for each iteration. TensorBoard provides a visual presenation of iterations. 

The logs of the training are uploaded to a Google Cloud Storage Bucket. TensorBoard automatically references this log location and displays the corresponding data. 

The training component contains a TensorBoard visualization (TensorBoard viewer), which makes is comfortable to open the TensorBoard session for training jobs.

To open TensorBoard click on the `training` component in your experiment run. Located on the ride side is the artifact windows which shows a very handy button called (Open TensorBoard).

In order to use his visualizations, your pipeline component must write a JSON file. Kubeflow provides a good documenation on [how visualizations are working](https://www.kubeflow.org/docs/pipelines/sdk/output-viewer/) and what types are available.

```
# write out TensorBoard viewer
metadata = {
    'outputs' : [{
      'type': 'tensorboard',
      'source': args.input_job_dir,
    }]
}

with open('/mlpipeline-ui-metadata.json', 'w') as f:
  json.dump(metadata, f)
```

## Training metrics

Your training component creates a metric (accuracy-score) which are displayed in the experiment UI. With those metrics, you can compare your different runs and model performance.

![metrics](files/metrics.png)

*Next*: [Predict](step-7-predictions.md)

*Previous*: [Run the pipeline](step-5-run-pipeline.md)