KUBEFLOW=https://storage.googleapis.com/ml-pipeline/release/0.1.20/kfp.tar.gz

all: components pipeline 

.PHONY: venv
venv:
	@test -d ./venv || python3 -m venv venv
	@. ./venv/bin/activate && pip install $(KUBEFLOW) --upgrade

.PHONY: pipeline
pipeline:
	@. ./venv/bin/activate && python create_pipeline.py

.PHONY: components
components:
	@(cd ./components/bq2gcs && make)
	@(cd ./components/trainjob && make)
	@(cd ./components/deploymodel && make)

.PHONY: pyclean
pyclean:
	@find . -name '*.pyc' -delete

.PHONY: clean
clean: pyclean
	@rm -r ./venv text2hub.tar.gz || echo OK
	@(cd ./components/bq2gcs && make clean)
	@(cd ./components/trainjob && make clean)
	@(cd ./components/deploymodel && make clean)
