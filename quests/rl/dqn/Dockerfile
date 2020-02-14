FROM gcr.io/deeplearning-platform-release/tf2-gpu:m40
RUN apt-get update
RUN apt-get install --yes python3-pip ffmpeg xvfb python-opengl swig libglu1-mesa-dev freeglut3-dev mesa-common-dev
RUN yes | python3 -m pip install --upgrade --quiet tf-nightly-2.0-preview pip
RUN python3 -m pip install gym[box2d]==0.15.3 cloudml-hypertune==0.1.0.dev5 \
    PyVirtualDisplay==0.2.4 pyglet==1.3.2
ENV PYTHONPATH="/root/.local/lib/python3.6/site-packages:$PYTHONPATH"
COPY trainer /trainer
COPY train_model.sh train_model.sh
RUN chmod +x train_model.sh
ENTRYPOINT ["bash", "train_model.sh"]