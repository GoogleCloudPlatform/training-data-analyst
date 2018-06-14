# Operations and Best Practices

![Module-2. Lab Diagram](https://github.com/henrybell/advanced-kubernetes-bootcamp/blob/master/module-2/diagrams/lab-diag.png)*Module-2. Lab Diagram*

# Lab Outline

**Total estimated time: 1 hr 30 mins**

## Tools and Repo

+  Clone Repo with workshop files
+  Install following tools in Cloud Shell
    
    +  `Helm` for application management
    +  `kubectx/kubens` for easy context switching

## Kubernetes Multicluster Architecture (30 mins)

+  Deploy three Kubernetes Engine clusters (5 mins)

    +  Use gcloud
    +  Two clusters (`cluster-1` and `cluster-2`) used for multi-cluster and application deployment
    +  One cluster (`cluster-3`) used for Spinnaker, NGINX LB and Container Registry

+  Install Istio on all three clusters (5 mins)

    +  Use latest release artifacts (0.8 and onwards will have LTS)
    +  Use Helm
    +  Enable sidecar injector for `cluster-1` and `cluster-2` for the `default` namespace
    +  For using _Ingress_ and _RouteRules_ later in the lab

+  Install and configure Spinnaker on `cluster-3` (20 mins)

    +  Create service accounts and GCS buckets
    +  Create secret with kubeconfig
    +  Create spinnaker config
    +  Use helm charts by Vic (***chart deployment takes about 10 mins***)

## Application lifecycle management with Spinnaker (20 mins)

+  Prepare Container Registry (5 mins)
    +  Push a simple `web-server` app to Container Registry with version tag `v1.0.0`
    +  Push `busyboxplus` to Container registry to simulate canary testing
    
+  Configure a **Deploy** pipeline in Spinnaker to deploy a web app to both clusters (5 mins)

    +  Deploy Canary > Test Canary > Manual Judgement > Deploy to Prod 
    +  Triggered via version tag (`v.*`) from Container Registry

+  Manually deploy pipeline for `v1.0.0` to `cluster-1` and `cluster-2` (10 mins)

## Load Balancing traffic to cluster-1 and cluster-2 (15 mins)

+  Load balance traffic using an NGINX load balancer to both `cluster-1` and `cluster-2` (10 mins)

    +  Install NGINX LB in `cluster-3` (outside of `cluster-1` and `cluster-2`)
    +  Configure a ConfigMap for `load-balancer.conf` with `cluster-1` and `cluster-2` Ingress IP addresses pointing to the webapp
    +  Expose NGINX as `Type:LoadBalancer` for Client access
    +  Manipulate `weight` fields in the ConfigMap to manage traffic between `cluster-1` and `cluster-2` 

## Triggering application updates with Spinnaker (15 mins)

+  Trigger the **Deploy** pipeline by updating the version tag to `v1.0.1` in Container Registry (15 mins)

## Traffic management to prod and canary using Istio (10 mins)

+  Use _RouteRules_ to route traffic between _prod_ and _canary_ releases within each cluster (10 mins)

# Lab Guide

[Lab Guide](lab_guide.md)

# Presentations

Dependent upon labs

# Lab Materials and Useful Links

[Multicloud TAW - Modules 2, 3, 4, and 5](https://docs.google.com/document/d/1FnNiKuS5K6J8Lct2qStQ1N8r8gR3snc7TaDzPDgIODw/edit)

[Multicloud Workshop Presentation](https://docs.google.com/presentation/d/1gLWKMZr9U6AqtjyxH2LFE7m03ZWFnjjrarj4nS7_s6c/edit#slide=id.g2dfddef4d5_0_1435)  

[Continuous Delivery with Spinnaker on Kubernetes Engine](https://cloud.google.com/solutions/continuous-delivery-spinnaker-kubernetes-engine)

[Istio Route Rules](https://istio.io/docs/concepts/traffic-management/rules-configuration.html)
