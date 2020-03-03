# This container is for running ksonnet within Kubernetes
FROM ubuntu:16.04

ENV KUBECTL_VERSION v1.9.2
ENV KSONNET_VERSION 0.10.1

RUN apt-get update && apt-get -y install curl && rm -rf /var/lib/apt/lists/*
#RUN apk add --update ca-certificates openssl && update-ca-certificates

RUN curl -O -L https://github.com/ksonnet/ksonnet/releases/download/v${KSONNET_VERSION}/ks_${KSONNET_VERSION}_linux_amd64.tar.gz
RUN tar -zxvf ks_${KSONNET_VERSION}_linux_amd64.tar.gz -C /usr/bin/ --strip-components=1 ks_${KSONNET_VERSION}_linux_amd64/ks  
RUN chmod +x /usr/bin/ks

RUN curl -L  https://storage.googleapis.com/kubernetes-release/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl  -o /usr/bin/kubectl
RUN chmod +x /usr/bin/kubectl

#ksonnet doesn't work without a kubeconfig, the following is just to add a utility to generate a kubeconfig from a service account.
ADD https://raw.githubusercontent.com/zlabjp/kubernetes-scripts/cb265de1d4c4dc4ad0f15f4aaaf5b936dcf639a5/create-kubeconfig /usr/bin/
ADD https://raw.githubusercontent.com/zlabjp/kubernetes-scripts/cb265de1d4c4dc4ad0f15f4aaaf5b936dcf639a5/LICENSE.txt /usr/bin/create-kubeconfig.LICENSE
RUN chmod +x /usr/bin/create-kubeconfig

RUN kubectl config set-context default --cluster=default
RUN kubectl config use-context default

ENV USER root

ADD ksonnet-entrypoint.sh /
RUN chmod +x /ksonnet-entrypoint.sh

ENTRYPOINT ["/ksonnet-entrypoint.sh"]
