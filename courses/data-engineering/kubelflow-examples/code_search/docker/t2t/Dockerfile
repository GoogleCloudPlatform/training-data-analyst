ARG BASE_IMAGE_TAG=1.8.0

FROM tensorflow/tensorflow:$BASE_IMAGE_TAG

RUN pip --no-cache-dir install oauth2client~=4.1.0 &&\
    apt-get update && apt-get install -y jq git python3-pip &&\
    rm -rf /var/lib/apt/lists/*

RUN pip --no-cache-dir install \
	tensor2tensor~=1.10.0 \
	tensorflow-hub~=0.1.1 \
	six

RUN pip3 --no-cache-dir install \
	tensor2tensor~=1.10.0 \
	tensorflow-hub~=0.1.1 \
	six

ADD src/code_search /app/code_search
ADD src             /src

ADD docker/t2t/t2t-entrypoint.sh /usr/local/sbin/t2t-entrypoint
ADD docker/t2t/run_and_wait.sh /usr/local/sbin/run_and_wait.sh
RUN chmod a+x /usr/local/sbin/run_and_wait.sh

WORKDIR /app

ENV PYTHONIOENCODING=utf-8 T2T_USR_DIR=/app/code_search/t2t

VOLUME ["/data", "/output"]

