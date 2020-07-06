FROM gcr.io/deeplearning-platform-release/tf2-cpu.2-1
COPY requirements.txt .
RUN python -m pip install -U -r requirements.txt

ENTRYPOINT ["tfx"]
