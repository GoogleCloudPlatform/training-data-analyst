FROM gcr.io/deeplearning-platform-release/tf2-cpu
COPY trainer /babyweight/trainer
RUN apt update && \
    apt install --yes python3-pip && \
    pip3 install --upgrade --quiet tensorflow==2.0

ENV PYTHONPATH ${PYTHONPATH}:/babyweight
ENTRYPOINT ["python3", "babyweight/trainer/task.py"]