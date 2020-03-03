# Makefile for building images
#
# To override variables do
# make ${TARGET} ${VAR}=${VALUE}
#
# Examples:
# make build-s2i-image IMG=gcr.io/kubeflow-examples/xgboost_ames_housing_s2i TAG=test
# make build-seldon-image IMG=gcr.io/kubeflow-examples/xgboost_ames_housing_seldon TAG=latest SOURCE=../seldon_serve

# List any changed  files. We only include files in the notebooks directory.
# because that is the code in the docker image.
# In particular we exclude changes to the ksonnet configs.
CHANGED_FILES := $(shell git diff-files --relative=code_search)

ifeq ($(strip $(CHANGED_FILES)),)
# Changed files is empty; not dirty
# Don't include --dirty because it could be dirty if files outside the ones we care
# about changed.
GIT_VERSION := $(shell git log --pretty=format:'%h' -n 1)
else
GIT_VERSION := $(shell git log --pretty=format:'%h' -n 1)-dirty-$(shell git diff | shasum -a256 | cut -c -6)
endif

# Build a image which contains source-to-image tool used by seldon for making
# image to serve models. This image should be stable and doesn't need to
# rebuild often.
build-s2i-image:IMG?=gcr.io/kubeflow-examples/xgboost_ames_housing_s2i
build-s2i-image:TAG?=latest
build-s2i-image:
	@echo IMG=$(IMG)
	@echo GIT_VERSION=$(GIT_VERSION)
	@echo TAG=$(TAG)
	docker build -f "./Dockerfile.ubuntu-s2i" \
             -t $(IMG):$(TAG) \
             --label=git-versions=$(GIT_VERSION) \
             ./
	@echo Built $(IMG):$(TAG)

# Build a serving image in a s2i image, which can be built in the above step.
build-seldon-image:IMG?=gcr.io/kubeflow-examples/xgboost_ames_housing_seldon
build-seldon-image:TAG?=latest
build-seldon-image:SOURCE?=../seldon_serve
build-seldon-image:
	@echo IMG=$(IMG)
	@echo GIT_VERSION=$(GIT_VERSION)
	@echo TAG=$(TAG)
	@echo SOURCE=$(SOURCE)
	gcloud builds submit \
		--config seldon-image-build.yaml \
		--substitutions=_IMG=$(IMG),TAG_NAME=$(TAG),_GIT_VERSION=$(GIT_VERSION) \
		$(SOURCE)
	@echo Built $(IMG):$(TAG)
