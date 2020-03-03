FROM python:2.7-jessie

RUN apt-get update && apt-get install -y curl &&\
    rm -rf /var/lib/apt/lists/*

RUN curl -sL https://deb.nodesource.com/setup_10.x | bash - &&\
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

COPY src/requirements.ui.txt /tmp/requirements.ui.txt
COPY src/requirements.nmslib.txt /tmp/requirements.nmslib.txt
RUN pip install -r /tmp/requirements.ui.txt
RUN pip install -r /tmp/requirements.nmslib.txt

ADD src/ /src

WORKDIR /src

ARG PUBLIC_URL

ENV PUBLIC_URL=$PUBLIC_URL

RUN cd ui && npm i && npm run build && cd ..

EXPOSE 8008

ENTRYPOINT ["python"]
