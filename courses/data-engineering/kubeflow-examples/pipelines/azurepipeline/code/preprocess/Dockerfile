FROM tensorflow/tensorflow:2.0.0a0-gpu-py3

# pip install
COPY requirements.txt /scripts/requirements.txt
RUN pip install -r /scripts/requirements.txt

COPY data.py /scripts/data.py

# will be overwritten by kf pipeline
ENTRYPOINT [ "python", "/scripts/data.py" ]
