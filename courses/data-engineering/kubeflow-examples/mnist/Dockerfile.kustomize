# This container is for running kustomize within Kubernetes
FROM ubuntu:16.04

ENV KUBECTL_VERSION v1.9.2
ENV KUSTOMIZE_VERSION 2.0.3

RUN apt-get update && apt-get -y install curl && rm -rf /var/lib/apt/lists/*
#RUN apk add --update ca-certificates openssl && update-ca-certificates

RUN curl -O -L https://github.com/kubernetes-sigs/kustomize/releases/download/v${KUSTOMIZE_VERSION}/kustomize_${KUSTOMIZE_VERSION}_linux_amd64
RUN mv kustomize_${KUSTOMIZE_VERSION}_linux_amd64 /usr/bin/kustomize
RUN chmod +x /usr/bin/kustomize

RUN curl -L  https://storage.googleapis.com/kubernetes-release/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl  -o /usr/bin/kubectl
RUN chmod +x /usr/bin/kubectl

# The following is just to add a utility to generate a kubeconfig from a service account.
ADD https://raw.githubusercontent.com/zlabjp/kubernetes-scripts/cb265de1d4c4dc4ad0f15f4aaaf5b936dcf639a5/create-kubeconfig /usr/bin/
ADD https://raw.githubusercontent.com/zlabjp/kubernetes-scripts/cb265de1d4c4dc4ad0f15f4aaaf5b936dcf639a5/LICENSE.txt /usr/bin/create-kubeconfig.LICENSE
RUN chmod +x /usr/bin/create-kubeconfig

RUN kubectl config set-context default --cluster=default
RUN kubectl config use-context default

ENV USER root

ADD kustomize-entrypoint.sh /
RUN chmod +x /kustomize-entrypoint.sh

ENTRYPOINT ["/kustomize-entrypoint.sh"]
