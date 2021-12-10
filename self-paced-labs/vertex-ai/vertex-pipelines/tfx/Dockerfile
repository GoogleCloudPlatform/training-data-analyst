# Specifies base image and tag.
FROM gcr.io/tfx-oss-public/tfx:1.4.0

# Copies the requirements.txt into the container to reduce network calls.
COPY requirements.txt requirements.txt
# Installs additional packages.
RUN pip install -r requirements.txt

# Copies the pipeline code to the docker image.
COPY tfx_taxifare_tips/ tfx_taxifare_tips/

ENV PYTHONPATH="/tfx_taxifare_tips:${PYTHONPATH}"