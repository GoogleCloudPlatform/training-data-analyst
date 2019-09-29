FROM gcr.io/deeplearning-platform-release/tf2-cpu

COPY . /code

RUN apt-get update && \
    apt-get install --yes python3-pip && \
    pip3 install /code 


ENTRYPOINT ["python3", "/code/trainer/task.py"]
