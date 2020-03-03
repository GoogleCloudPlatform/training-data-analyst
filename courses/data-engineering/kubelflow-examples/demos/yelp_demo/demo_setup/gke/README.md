# GKE Cluster and Type

## Overview

This is a [Google Cloud Deployment
Manager](https://cloud.google.com/deployment-manager/overview) template which
deploys a GKE cluster and a Deployment Manager type. The type can be used by
other deployments to deploy Kubernetes resources into the cluster.

## Getting started

Using Deployment Manager to deploy Kubernetes resources into a new GKE cluster
is a two step process, as described below.

### Deploy a cluster

Using `cluster.yaml`, deploy a GKE cluster to use for deploying the solution
later. Fill in the following information before deploying:

* zone in which to run the cluster
* basicauth username and password for authenticating access to the cluster

When ready, deploy with the following command:

    gcloud deployment-manager deployments create gke-cluster --config cluster.yaml

This will result in two resources:

* a GKE cluster named `gke-cluster-my-cluster`
* a Deployment Manager type named `gke-cluster-my-cluster-type`

The type can now be used in other deployments to deploy kubernetes resources
using the cluster API.

### Deploying Kubernetes resources

Using `replicatedservice.yaml`, deploy a `Service` and a `ReplicationController`
to the GKE cluster created in the last step. Fill in the following information
before deploying:

* The cluster type created for the GKE cluster deployed previously. This will
  be `gke-cluster-my-cluster-type`, visible in the developers console.
* Optionally, change the `docker` image to run.
* Optionally, specify the port exposed by the image.

When ready, deploy with the following command:

    gcloud deployment-manager deployments create rs --config replicatedservice.yaml

### Verifying deployment

Be sure your `kubectl` command-line tool is set up to communicate with the
cluster you have deployed:

    gcloud container clusters get-credentials gke-cluster-my-cluster --zone <zone>

Now you can see the resources that have been deployed using `kubectl`:

    kubectl get rc
    kubectl get services

Once the `EXTERNAL_IP` is available for your service, you can test it:

    curl <ip address>:8080

## Important Note

When deploying into a Kubernetes cluster with Deployment Manager, it is
important to be aware that deleting `ReplicationController` Kubernetes objects
**does not delete its underlying pods**, and it is your responisibility to
manage the destruction of these resources when deleting or updating a
`ReplicationController` in your configuration.

