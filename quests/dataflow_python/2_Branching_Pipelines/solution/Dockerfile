FROM gcr.io/dataflow-templates-base/python3-template-launcher-base

ARG WORKDIR=/dataflow/template
RUN mkdir -p ${WORKDIR}
WORKDIR ${WORKDIR}

RUN apt-get update && apt-get install -y libffi-dev && rm -rf /var/lib/apt/lists/*

COPY my_pipeline.py .

ENV FLEX_TEMPLATE_PYTHON_PY_FILE="${WORKDIR}/my_pipeline.py"

RUN python3 -m pip install apache-beam[gcp]==2.25.0
