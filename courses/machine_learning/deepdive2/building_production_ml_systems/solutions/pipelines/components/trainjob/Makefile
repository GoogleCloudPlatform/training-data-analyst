all: clean substitute build push

.PHONY: pyclean
pyclean:
	@find . -name '*.pyc' -delete
	@find . -name '*.pytest_cache' -delete
	@find . -name '__pycache__' -delete
	@find . -name '*egg-info' -delete

.PHONY: clean
clean: pyclean
	@rm -r ./venv ./component.yaml || echo OK

.PHONY: build
build: pyclean
	@./scripts/build.sh

.PHONY: push
push: 
	@./scripts/push.sh

.PHONY: login
login: 
	@./scripts/login.sh

.PHONY: test
test: 
	@./scripts/test.sh

.PHONY: substitute
substitute: 
	@./scripts/substitute.sh
