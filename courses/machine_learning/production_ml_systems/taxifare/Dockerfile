FROM gcr.io/deeplearning-platform-release/tf2-cpu

COPY trainer /trainer

RUN apt update && \
    apt install --yes python3-pip && \
    pip3 install /trainer 


ENTRYPOINT ["python3", "/trainer/task.py"]
