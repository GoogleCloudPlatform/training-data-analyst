all: venv

.PHONY: venv
venv:
	@test -d ./venv || python3 -m venv venv
	@. ./venv/bin/activate && pip install -U pip && pip install -e . 

.PHONY: pyclean
pyclean:
	@find . -name '*.pyc' -delete
	@find . -name '*.pytest_cache' -delete
	@find . -name '__pycache__' -delete
	@find . -name '*egg-info' -delete

.PHONY: clean
clean: pyclean
	@rm -r ./venv || echo OK
