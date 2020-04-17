# Demo: Creating a Hadoop Cluster with Cloud Dataproc

Cloud Dataproc is a fast, easy-to-use, fully-managed cloud service for running  [Apache Spark](http://spark.apache.org/) and  [Apache Hadoop](http://hadoop.apache.org/) clusters in a simpler, more cost-efficient way. Operations that used to take hours or days take seconds or minutes instead. Create Cloud Dataproc clusters quickly and resize them at any time, so you don't have to worry about your data pipelines outgrowing your clusters.

This demo shows you how to use the Google Cloud Platform (GCP) Console to create a Google Cloud Dataproc cluster, run a simple  [Apache Spark](http://spark.apache.org/) job in the cluster, then modify the number of workers in the cluster.

### Confirm __Cloud Dataproc API is enabled__

To create a Dataproc cluster in GCP, the Cloud Dataproc API must be enabled. To confirm the API is enabled:

Click __Navigation menu__ > __APIs & Services__ > __Library__:

Type __Cloud Dataproc__ in the __Search for APIs & Services__ dialog. The console will display the Cloud Dataproc API in the search results.

Click on __Cloud Dataproc API__ to display the status of the API. If the API is not already enabled, click the __Enable__ button.

If the API's enabled, you're good to go.

## Create a cluster

In the Cloud Platform Console, select __Navigation menu__ > __Dataproc__ > __Clusters__, then click __Create cluster__.

Set the following fields for your cluster. Accept the default values for all other fields.

Field | Value
--- | ---
Name | example-cluster
Region | global
Zone | us-central1-a

<aside>
<strong>Note:</strong> A *Zone* is a special multi-region namespace that is capable of deploying instances into all Google Compute zones globally. You can also specify distinct regions, such as `us-east1` or `europe-west1`, to isolate resources (including VM instances and Google Cloud Storage) and metadata storage locations utilized by Cloud Dataproc within the user-specified region.
</aside>

Click __Create__ to create the cluster.

Your new cluster will appear in the Clusters list. It may take a few minutes to create, the cluster Status shows as "Provisioning" until the cluster is ready to use, then changes to "Running."


## Submit a job

To run a sample Spark job:

Click __Jobs__ in the left pane to switch to Dataproc's jobs view, then click __Submit job__:

Set the following fields to update Job. Accept the default values for all other fields.

Field | Value
--- | ---
Cluster | example-cluster
Job type | Spark
Main class or jar | org.apache.spark.examples.SparkPi
Arguments | 1000 (This sets the number of tasks.)
Jar file | file:///usr/lib/spark/examples/jars/spark-examples.jar

Click __Submit__.

<aside class="special"><p><strong>How the job calculates Pi:</strong> The Spark job estimates a value of Pi using the <a href="https://en.wikipedia.org/wiki/Monte_Carlo_method" target="_blank">Monte Carlo method</a>. It generates x,y points on a coordinate plane that models a circle enclosed by a unit square. The input argument (1000) determines the number of x,y pairs to generate; the more pairs generated, the greater the accuracy of the estimation. This estimation leverages Cloud Dataproc worker nodes to parallelize the computation. For more information, see <a href="https://academo.org/demos/estimating-pi-monte-carlo/" target="_blank">Estimating Pi using the Monte Carlo Method</a> and see <a href="https://github.com/apache/spark/blob/master/examples/src/main/java/org/apache/spark/examples/JavaSparkPi.java" target="_blank">JavaSparkPi.java on GitHub</a>.</p>
</aside>

Your job should appear in the __Jobs__ list, which shows your project's jobs with its cluster, type, and current status. Job status displays as __Running__, and then __Succeeded__ after it completes.


## View the job output

To see your completed job's output:

Click the job ID in the __Jobs__ list.

Check __Line wrapping__ or scroll all the way to the right to see the calculated value of Pi. Your output, with __Line wrapping__ checked should show the value of Pi.

Your job has successfully calculated a rough value for pi!


### Optional Demo: Update a cluster

To change the number of worker instances in your cluster:

1. Select __Clusters__ in the left navigation pane to return to the Dataproc Clusters view.
2. Click __example-cluster__ in the __Clusters__ list. By default, the page displays an overview of your cluster's CPU usage.
3. Click __Configuration__ to display your cluster's current settings.

4. Click __Edit__. The number of worker nodes is now editable.
5. Enter __4__ in the __Worker nodes__ field.
6. Click __Save__.

Your cluster is now updated. Check out the number of VM instances in the cluster

To rerun the job with the updated cluster, you would click __Jobs__ in the left pane, then click __SUBMIT JOB__.

Set the same fields you set in the __Submit a job__ section:

Field | Value
--- | ---
Cluster | example-cluster
Job type | Spark
Main class or jar | org.apache.spark.examples.SparkPi
Arguments | 1000 (This sets the number of tasks.)
Jar file | file:///usr/lib/spark/examples/jars/spark-examples.jar

Click __Submit__.


## Congratulations!
Now you know how to use the Google Cloud Platform Console to create and update a Dataproc cluster and then submit a job in that cluster.