FROM gcr.io/tfx-oss-public/tfx:1.4.0

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY tfx_taxifare_tips/ tfx_taxifare_tips/

ENV PYTHONPATH="/pipeline:${PYTHONPATH}"