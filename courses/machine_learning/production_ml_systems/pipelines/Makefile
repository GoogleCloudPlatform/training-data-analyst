KUBEFLOW=https://storage.googleapis.com/ml-pipeline/release/0.1.20/kfp.tar.gz

all: venv pipeline

.PHONY: venv
venv:
	@test -d ./venv || python3 -m venv venv
	@. ./venv/bin/activate && pip install $(KUBEFLOW) --upgrade

.PHONY: pipeline
pipeline:
	@. ./venv/bin/activate && python create_pipeline.py

.PHONY: pyclean
pyclean:
	@find . -name '*.pyc' -delete

.PHONY: clean
clean: pyclean
	@rm -r ./venv text2hub.tar.gz || echo OK
