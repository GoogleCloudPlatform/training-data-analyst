# Specifies base image and tag.
# https://cloud.google.com/vertex-ai/docs/training/pre-built-containers
FROM gcr.io/deeplearning-platform-release/tf2-cpu.2-3
WORKDIR /root

COPY requirements.txt .
# Installs additional packages.
RUN pip3 install -U -r requirements.txt

# Copies the trainer code to the docker image.
COPY task.py /root/task.py

# Sets up the entry point to invoke the trainer.
ENTRYPOINT ["python3", "task.py"]

