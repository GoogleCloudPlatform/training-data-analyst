FROM tensorflow/tensorflow:2.0.0a0-gpu-py3
RUN pip install azure-cli
RUN az extension add -n azure-cli-ml
RUN pip install --upgrade pip
RUN pip install --upgrade pillow
RUN pip install azureml
RUN pip install azureml.core
COPY profile.sh /scripts/profile.sh
COPY inferenceconfig.json /scripts/inferenceconfig.json
COPY score.py /scripts/score.py
COPY environment.yml /scripts/environment.yml
ENTRYPOINT bash