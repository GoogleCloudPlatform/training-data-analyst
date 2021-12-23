# Specifies base image and tag.
# https://cloud.google.com/vertex-ai/docs/training/pre-built-containers
FROM us-docker.pkg.dev/vertex-ai/training/tf-cpu.2-6:latest

# Sets the container working directory.
WORKDIR /root

# Copies the requirements.txt into the container to reduce network calls.
COPY requirements.txt .

# Installs additional packages.
RUN pip3 install -U -r requirements.txt

# b/203105209 Removes unneeded file from TF2.5 CPU image for python_module CustomJob training. 
# Will be removed on subsequent public Vertex images.
RUN rm -rf /var/sitecustomize/sitecustomize.py

# Copies the trainer code to the docker image.
COPY . /trainer

# Sets the container working directory.
WORKDIR /trainer

# Sets up the entry point to invoke the trainer.
ENTRYPOINT ["python", "-m", "trainer.task"]
