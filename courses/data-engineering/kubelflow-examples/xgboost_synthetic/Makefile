# IMG is the base path for images..
# Individual images will be
# $(IMG)/$(NAME):$(TAG)

PROJECT ?= code-search-demo
IMG ?= gcr.io/${PROJECT}/xgboost-synthetic/notebook
GITOPS_IMAGE ?= gcr.io/${PROJECT}/xgboost-synthetic/gitops

# List any changed  files. We only include files in the notebooks directory.
# because that is the code in the docker image.
# In particular we exclude changes to the ksonnet configs.
CHANGED_FILES := $(shell git diff-files)

# Whether to use cached images with GCB
USE_IMAGE_CACHE ?= true

ifeq ($(strip $(CHANGED_FILES)),)
# Changed files is empty; not dirty
# Don't include --dirty because it could be dirty if files outside the ones we care
# about changed.
GIT_VERSION := $(shell git describe --always)
else
GIT_VERSION := $(shell git describe --always)-dirty-$(shell git diff | shasum -a256 | cut -c -6)
endif

TAG := $(shell date +v%Y%m%d)-$(GIT_VERSION)
all: build

# To build without the cache set the environment variable
# export DOCKER_BUILD_OPTS=--no-cache
.PHONY: build
build-dir: ./Dockerfile ./requirements.txt
	rm -rf ./.build
	mkdir  -p ./.build
	cp ./requirements.txt ./.build/
	cp ./Dockerfile* ./.build/

build: build-dir
	cd .build && docker build ${DOCKER_BUILD_OPTS} -t $(IMG):$(TAG) -f Dockerfile . \
           --label=git-verions=$(GIT_VERSION)
	docker tag $(IMG):$(TAG) $(IMG):latest
	@echo Built $(IMG):latest
	@echo Built $(IMG):$(TAG)

build-gcb: build-dir
	gcloud builds submit --machine-type=n1-highcpu-32 --project=$(PROJECT) --tag=$(IMG):$(TAG) \
		--timeout=3600 ./.build
	@echo Built $(IMG):$(TAG)

# Build but don't attach the latest tag. This allows manual testing/inspection of the image
# first.
push: build
	docker push $(IMG):$(TAG)
	docker push $(IMG):latest
	@echo Pushed $(IMG):$(TAG)
