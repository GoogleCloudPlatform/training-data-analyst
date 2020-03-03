FROM gcr.io/kubeflow-images-public/tensorflow-1.6.0-notebook-cpu
RUN pip install ktext==0.34
RUN pip install annoy
RUN pip install --upgrade google-cloud
RUN pip install sklearn h5py
RUN pip install nltk

COPY ./ /workdir/
