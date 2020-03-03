FROM debian:7

RUN apt-get update && apt-get install -y wget ca-certificates git-core &&\
    rm -rf /var/lib/apt/lists/*

RUN wget -O /tmp/hub-linux-amd64-2.6.0.tgz https://github.com/github/hub/releases/download/v2.6.0/hub-linux-amd64-2.6.0.tgz && \
	cd /usr/local && \
	tar -xvf /tmp/hub-linux-amd64-2.6.0.tgz && \
	ln -sf /usr/local/hub-linux-amd64-2.6.0/bin/hub /usr/local/bin/hub

RUN wget -O /opt/ks_0.12.0_linux_amd64.tar.gz \
      https://github.com/ksonnet/ksonnet/releases/download/v0.12.0/ks_0.12.0_linux_amd64.tar.gz && \
    tar -C /opt -xzf /opt/ks_0.12.0_linux_amd64.tar.gz && \
    cp /opt/ks_0.12.0_linux_amd64/ks /bin/. && \
    rm -f /opt/ks_0.12.0_linux_amd64.tar.gz && \
    wget -O /bin/kubectl \
      https://storage.googleapis.com/kubernetes-release/release/v1.11.2/bin/linux/amd64/kubectl && \
    chmod u+x /bin/kubectl

ADD kubeflow /usr/local/src
ADD docker/ks/*.sh /usr/local/src/

WORKDIR /usr/local/src
