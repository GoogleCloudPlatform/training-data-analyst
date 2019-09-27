FROM gcr.io/deeplearning-platform-release/tf2-cpu
RUN apt-get update
RUN apt-get install --yes python3-pip ffmpeg xvfb python-opengl
RUN pip3 install --upgrade --quiet tf-nightly-2.0-preview
RUN pip3 install --user gym==0.12.5 cloudml-hypertune==0.1.0.dev5 \
    PyVirtualDisplay==0.2.4 pyglet==1.3.2
ENV PYTHONPATH="/root/.local/lib/python3.6/site-packages:$PYTHONPATH"
COPY trainer /trainer
COPY train_model.sh train_model.sh
RUN chmod +x train_model.sh
ENTRYPOINT ["bash", "train_model.sh"]