FROM python:3.6
COPY ./workspace/src /workspace/src/ 
RUN apt-get update && apt-get install -y --no-install-recommends \
    python-pandas \
    && pip3 install -U scikit-learn \
    && pip3 install -U ktext \
    && pip3 install -U IPython \
    && pip3 install -U annoy \
    && pip3 install -U tqdm \
    && pip3 install -U nltk \
    && pip3 install -U matplotlib \
    && pip3 install -U tensorflow \
    && pip3 install -U bernoulli \
    && pip3 install -U h5py \
    && git clone https://github.com/google/seq2seq.git \
    && pip3 install -e ./seq2seq/ \
    && apt-get clean \
    && rm -rf \
        /var/lib/apt/lists/* \
        /tmp/* \
        /var/tmp/* \
        /usr/share/man \
        /usr/share/doc \
        /usr/share/doc-base
