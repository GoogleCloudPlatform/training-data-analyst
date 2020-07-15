FROM google/cloud-sdk:latest

COPY . /code
WORKDIR /code

RUN pip3 install cloudml-hypertune

ENTRYPOINT ["./main.sh"]
