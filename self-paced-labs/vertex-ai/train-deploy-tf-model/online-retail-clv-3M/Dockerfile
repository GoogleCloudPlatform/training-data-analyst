# Specifies base image and tag.
# https://cloud.google.com/vertex-ai/docs/training/pre-built-containers
# us-docker.pkg.dev/vertex-ai/training/tf-cpu.2-3:latest
FROM gcr.io/deeplearning-platform-release/tf2-cpu.2-3

# Sets the container working directory.
WORKDIR /root

# Copies the requirements.txt into the container to reduce network calls.
COPY requirements.txt .
# Installs additional packages.
RUN pip3 install -U -r requirements.txt

# Copies the trainer code to the docker image.
COPY . /trainer

# Sets the container working directory.
WORKDIR /trainer

# Sets up the entry point to invoke the trainer.
ENTRYPOINT ["python", "-m", "trainer.task"]
