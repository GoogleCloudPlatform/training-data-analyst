FROM gcr.io/deeplearning-platform-release/tf2-cpu
COPY trainer /trainer
RUN apt-get update
RUN apt-get install --yes python3-pip ffmpeg xvfb
RUN pip3 install --upgrade --quiet tf-nightly-2.0-preview
RUN pip3 install --user gym==0.12.5 cloudml-hypertune==0.1.0.dev5 \
    PyVirtualDisplay==0.2.4 pyglet==1.3.2
CMD ["python3", "-m", "trainer.trainer"]