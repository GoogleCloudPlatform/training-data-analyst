# MNIST Pipelines GCP

This document describes how to run the [MNIST example](https://github.com/kubeflow/examples/tree/master/mnist) on Kubeflow Pipelines on a Google Cloud Platform and on premise cluster.

## Setup

### GCP

#### Create a GCS bucket

This pipeline requires a [Google Cloud Storage bucket](https://cloud.google.com/storage/) to hold your trained model. You can create one with the following command
```
BUCKET_NAME=kubeflow-pipeline-demo-$(date +%s)
gsutil mb gs://$BUCKET_NAME/
```

#### Deploy Kubeflow

Follow the [Getting Started Guide](https://www.kubeflow.org/docs/started/getting-started-gke) to deploy a Kubeflow cluster to GKE

#### Open the Kubeflow Pipelines UI

![Kubeflow UI](./img/kubeflow.png "Kubeflow UI")

##### IAP enabled
If you set up your cluster with IAP enabled as described in the [GKE Getting Started guide](https://www.kubeflow.org/docs/started/getting-started-gke), 
you can now access the Kubeflow Pipelines UI at `https://<deployment_name>.endpoints.<project>.cloud.goog/pipeline`

##### IAP disabled
If you opted to skip IAP, you can open a connection to the UI using *kubectl port-forward* and browsing to http://localhost:8085/pipeline

```
kubectl port-forward -n kubeflow $(kubectl get pods -n kubeflow --selector=service=ambassador \
    -o jsonpath='{.items[0].metadata.name}') 8085:80
```

### On Premise Cluster
For on premise cluster, beside of Kubeflow deployment, you need to create a [Persistent Volume (PV)](https://kubernetes.io/docs/concepts/storage/persistent-volumes/) and [Persistent Volume Claims(PVC)](https://kubernetes.io/docs/concepts/storage/persistent-volumes/#persistentvolumeclaims) to store trained result. 
Note that the `accessModes` of the PVC should be `ReadWriteMany ` so that the PVC can be mounted by containers of multiple steps in parallel.

### Install Python Dependencies

Set up a [virtual environment](https://docs.python.org/3/tutorial/venv.html) for your Kubeflow Pipelines work:

```
python3 -m venv $(pwd)/venv
source ./venv/bin/activate
```

Install the Kubeflow Pipelines sdk, along with other Python dependencies in the [requirements.txt](./requirements.txt) file

```
pip install -r requirements.txt --upgrade
```

## Running the Pipeline

#### Compile Pipeline
Pipelines are written in Python, but they must be compiled into a [domain-specific language (DSL)](https://en.wikipedia.org/wiki/Domain-specific_language) before they can be used. 

For on premise cluster, update the `platform` to `onprem` in `mnist_pipeline.py`.

```bash
sed -i.sedbak s"/platform = 'GCP'/platform = 'onprem'/"  mnist_pipeline.py
```

Most pipelines are designed so that simply running the script will preform the compilation steps:
```
python3 mnist_pipeline.py
```
Running this command should produce a compiled * mnist_pipeline.py.tar.gz* file:

Additionally, you can compile manually using the *dsl-compile* script

```
python venv/bin/dsl-compile --py mnist_pipeline.py --output mnist_pipeline.py.tar.gz
```

#### Upload through the UI

Now that you have the compiled pipelines file, you can upload it through the Kubeflow Pipelines UI.
Simply select the "Upload pipeline" button

![Upload Button](./img/upload_btn.png "Upload Button")

Upload your file and give it a name

![Upload Form](./img/upload_form.png "Upload Form")

#### Run the Pipeline

After clicking on the newly created pipeline, you should be presented with an overview of the pipeline graph.
When you're ready, select the "Create Run" button to launch the pipeline

![Pipeline](./img/pipeline.png "Pipeline")

Fill out the information required for the run, and press "Start" when you are ready.
 - GCP: Fill out the GCP `$BUCKET_ID` you created earlier, and ignore the option `pvc_name`.
 - On premise cluster: Fill out the `pvc_name` as name of the PVC you created earlier, and the PVC is mounted to '/mnt', so the `model-export-dir` can be `/mnt/export`.

![Run Form](./img/run_form.png "Run Form")

After clicking on the newly created Run, you should see the pipeline run through the 'train', 'serve', and 'web-ui' components. Click on any component to see its logs.
When the pipeline is complete, look at the logs for the web-ui component to find the IP address created for the MNIST web interface

![Logs](./img/logs.png "Logs")

## Pipeline Breakdown

Now that we've run a pipeline, lets break down how it works

#### Decorator
```
@dsl.pipeline(
    name='MNIST',
    description='A pipeline to train and serve the MNIST example.'
)
```
Pipelines are expected to include a `@dsl.pipeline` decorator to provide metadata about the pipeline

#### Function Header
```
def mnist_pipeline(model_export_dir='gs://your-bucket/export',
                   train_steps='200',
                   learning_rate='0.01',
                   batch_size='100'
                   pvc_name=''):
```
The pipeline is defined in the mnist_pipeline function. It includes a number of arguments, which are exposed in the Kubeflow Pipelines UI when creating a new Run. 
Although passed as strings, these arguments are of type [`kfp.dsl.PipelineParam`](https://github.com/kubeflow/pipelines/blob/master/sdk/python/kfp/dsl/_pipeline_param.py)

#### Train
```
train = dsl.ContainerOp(
    name='train',
    image='gcr.io/kubeflow-examples/mnist/model:v20190304-v0.2-176-g15d997b',
    arguments=[
        "/opt/model.py",
        "--tf-export-dir", model_export_dir,
        "--tf-train-steps", train_steps,
        "--tf-batch-size", batch_size,
        "--tf-learning-rate", learning_rate
        ]
)
```
This block defines the 'train' component. A component is made up of a [`kfp.dsl.ContainerOp`](https://github.com/kubeflow/pipelines/blob/master/sdk/python/kfp/dsl/_container_op.py) 
object with the container path and a name specified. The container image used is defined in the [Dockerfile.model in the MNIST example](https://github.com/kubeflow/examples/blob/master/mnist/Dockerfile.model)

After defining the train component, we also set a number of environment variables for the training script

#### Serve
```
serve = dsl.ContainerOp(
    name='serve',
    image='gcr.io/ml-pipeline/ml-pipeline-kubeflow-deployer:\
            7775692adf28d6f79098e76e839986c9ee55dd61',
    arguments=[
        '--model-export-path', model_export_dir,
        '--server-name', "mnist-service"
    ]
)
```
The 'serve' component is slightly different than 'train'. While 'train' runs a single container and then exits, 'serve' runs a container that launches long-living 
resources in the cluster. The ContainerOP takes two arguments: the path we exported our trained model to, and a server name. Using these, this pipeline component 
creates a Kubeflow [`tf-serving`](https://github.com/kubeflow/kubeflow/tree/master/kubeflow/tf-serving) service within the cluster. This service lives after the 
pipeline is complete, and can be seen using `kubectl get all -n kubeflow`. The Dockerfile used to build this container [can be found here](https://github.com/kubeflow/pipelines/blob/master/components/kubeflow/deployer/Dockerfile).

The `serve.after(train)` line specifies that this component is to run sequentially after 'train' is complete

#### Web UI
```
web_ui = dsl.ContainerOp(
    name='web-ui',
    image='gcr.io/kubeflow-examples/mnist/deploy-service:latest',
    arguments=[
        '--image', 'gcr.io/kubeflow-examples/mnist/web-ui:\
                v20190304-v0.2-176-g15d997b-pipelines',
        '--name', 'web-ui',
        '--container-port', '5000',
        '--service-port', '80',
        '--service-type', "LoadBalancer"
    ]
)

web_ui.after(serve)
``` 
Like 'serve', the web-ui component launches a service that exists after the pipeline is complete. Instead of launching a Kubeflow resource, the web-ui launches
a standard Kubernetes Deployment/Service pair. The Dockerfile that builds the deployment image [can be found here.](./deploy-service/Dockerfile) This image is used
to deploy the web UI, which was built from the [Dockerfile found in the MNIST example](https://github.com/kubeflow/examples/blob/master/mnist/web-ui/Dockerfile)

After this component is run, a new LoadBalancer is provisioned that gives external access to a 'web-ui' deployment launched in the cluster.

#### Main Function
```
 steps = [train, serve, web_ui]
  for step in steps:
    if platform == 'GCP':
      step.apply(gcp.use_gcp_secret('user-gcp-sa'))
    else:
      step.apply(onprem.mount_pvc(pvc_name, 'local-storage', '/mnt'))

if __name__ == '__main__':
    import kfp.compiler as compiler
    compiler.Compiler().compile(mnist_pipeline, __file__ + '.tar.gz')
```

For each step, if run under GCP, it is run with access to 'user-gcp-sa' secret, which gives read/write access to GCS resources (during training) and access to the 'kubectl' command within the container (during serving).

If run on premise, it is run with access to pvc_name that is passed in as pipeline argument.

At the bottom of the script is a main function. This is used to compile the pipeline when the script is run
