FROM gcr.io/deeplearning-platform-release/tf2-cpu
COPY babyweight_tf2 /babyweight_tf2
RUN apt update && \
    apt install --yes python3-pip && \
    pip3 install --upgrade --quiet tf-nightly-2.0-preview

ENV PYTHONPATH ${PYTHONPATH}:/babyweight_tf2
CMD ["python3", "-m", "trainer.task"]
