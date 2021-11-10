FROM gcr.io/deeplearning-platform-release/tf2-cpu

#RUN python3 -m pip install --upgrade --quiet tf-nightly-2.0-preview
RUN python3 -m pip install --upgrade --quiet cloudml-hypertune

COPY . /flights
ENV PYTHONPATH ${PYTHONPATH}:/flights
ENTRYPOINT ["python3", "-m", "trainer.task"]
