# Module 3 - Observability

## Prerequisites

* A running Kubernetes Engine cluster
* [Stackdriver Kubernetes Monitoring](https://cloud.google.com/monitoring/kubernetes-engine/installing) enabled for that cluster
* [Prometheus](https://cloud.google.com/monitoring/kubernetes-engine/prometheus) installed
* istio installed in the cluster
* The [Sock Shop](https://microservices-demo.github.io/) application installed

## Monitoring & Alerting

This lab draws heavily from the [StackDriver: Quick start](https://qwiklabs.com/focuses/559?locale=en&parent=catalog) lab.

1. Create Stackdriver account
2. Explore metrics from the GKE cluster
 * In StackDriver, go to Resources > Metrics Explorer
 * In "Resource type", choose `k8s_container`. In "Metric", choose
  `kubernetes.io/container/cpu/core_usage_time`.
 * Still in Metrics Explorer, change the "Metric" to
 `external.googleapis.com/prometheus/request_duration_seconds`, and group by
 `service`.
 * In StackDriver, go to Resources > Kubernetes and drill down in the
 Infrastructure tab, and then in Workloads and Services.
 * Select the front-end pod in the sock-shop namespace and inspect its metrics.
3. Create a logs-based metric
 * Still on front-end click on "VIEW LOGS" then "GO TO LOGGING"
 *  Append ` AND textPayload:"[31m500"` before closing ')'
 * Replace `resource.labels.pod_name="front-end-xxxxxxxxxx-xxxxx"` by
 `resource.labels.container_name="front-end"`
 * Click on "Create Metric" and choose the name `500s-frontend`
4. Create a simple StackDriver dashboard with the main metrics of the cluster
 * In the Dashboard menu, click on "Create Dashboard"
 * Give a name to the dashboard in clicking on Untitled Dashboard (like 500s)
 * Click on "Add Chart"
 * Give a name to the chart: `front-end errors`
 * In 'Find resource type and metrics' look for the metric you added:
 `500s-frontend`
 * Click save
5. Create an alert when error rate increase
 * On Stackdriver click on 'Alerting' -> 'Create a policy'
 * Click on 'Add condition'
 * Select 'Metric Threshold'
 * In resource type, select 'Log Metrics'
 * In configuration, IF METRIC select `user/500s-frontend` and set 1 to 'Threshold'
 * Then Save Condition
 * Click on 'Add Notification'
 * Add your email
 * Give a name to your policy
 * Like 'Alert on 500s'
6. Trigger the alert navigating the application
 * In the application, add a pair of socks to your basket
 * On the basket page, change the number of items to 0
 * Click on "Update basket"

## Debugging

This lab draws heavily from the [APM with StackDriver](https://events.qwiklab.com/labs/742/edit#step1) lab.

1. Discover the bug in the application
2. Go through Traces
3. Find the error in Error Reporting
4. View the error in Logging
5. Take a Snapshot to understand the bug
6. Add a Logpoint and observe the logs in Logging
