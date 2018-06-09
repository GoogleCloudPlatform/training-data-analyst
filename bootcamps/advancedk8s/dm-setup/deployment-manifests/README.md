# Installing sock-shop on Kubernetes

See the [documentation](https://microservices-demo.github.io/deployment/kubernetes.html) on how to deploy Sock Shop using Minikube.

## Kubernestes manifests

There are 2 sets of manifests for deploying Sock Shop on Kubernetes: one in the [manifests directory](manifests/), and complete-demo.yaml. The complete-demo.yaml is a single file manifest
made by concatenating all the manifests from the manifests directory, so please regenerate it when changing files in the manifests directory.

## Monitoring

All monitoring is performed by prometheus. All services expose a `/metrics` endpoint. All services have a Prometheus Histogram called `request_duration_seconds`, which is automatically appended to create the metrics `_count`, `_sum` and `_bucket`.

The manifests for the monitoring are spread across the [manifests-monitoring](./manifests-monitoring) and [manifests-alerting](./manifests-alerting/) directories.

To use them, please run `kubectl create -f <path to directory>`.

### What's Included?

* Sock-shop grafana dashboards
* Alertmanager with 500 alert connected to slack
* Prometheus with config to scrape all k8s pods, connected to local alertmanager.

### Ports

Grafana will be exposed on the NodePort `31300` and Prometheus is exposed on `31090`. If running on a real cluster, the easiest way to connect to these ports is by port forwarding in a ssh command:
```
ssh -i $KEY -L 3000:$NODE_IN_CLUSTER:31300 -L 9090:$NODE_IN_CLUSTER:31090 ubuntu@$BASTION_IP
```
Where all the pertinent information should be entered. Grafana and Prometheus will be available on `http://localhost:3000` or `:9090`.

If on Minikube, you can connect via the VM IP address and the NodePort.
