FROM google/cloud-sdk:latest

RUN apt-get update && \
    apt-get install --yes python3-pip

COPY . /code
WORKDIR /code

RUN pip3 install google-cloud-bigquery 


ENTRYPOINT ["python3", "./main.py"]
