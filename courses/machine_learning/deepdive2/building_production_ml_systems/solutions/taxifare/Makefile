all: clean build push

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

.PHONY: build
build: pyclean
	@./scripts/build.sh

.PHONY: push
push: 
	@./scripts/push.sh

.PHONY: submit
submit: 
	@./scripts/submit.sh

.PHONY: login
login: 
	@./scripts/login.sh

.PHONY: test
test: 
	@./scripts/test.sh
