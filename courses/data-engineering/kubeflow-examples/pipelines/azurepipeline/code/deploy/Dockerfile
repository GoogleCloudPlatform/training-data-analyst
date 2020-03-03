FROM mcr.microsoft.com/azure-cli
RUN az extension add -n azure-cli-ml
RUN pip install --upgrade pip
COPY deploymentconfig.json /scripts/deploymentconfig.json
COPY inferenceconfig.json /scripts/inferenceconfig.json
COPY deploy.sh /scripts/deploy.sh
COPY score.py /scripts/score.py
COPY environment.yml /scripts/environment.yml
CMD bash
