# Makefile for building images
#
# To override variables do
# make ${TARGET} ${VAR}=${VALUE}
IMG ?= gcr.io/kubeflow-examples/code-search

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

TAG := $(shell date +v%Y%m%d)-$(GIT_VERSION)
all: build

TF_VERSION=1.11.0


# Whether to use cached images with GCB
USE_IMAGE_CACHE ?= true

echo:
	@echo IMG=$(IMG)
	@echo GIT_VERSION=$(GIT_VERSION)
	@echo TAG=$(TAG)

# To build without the cache set the environment variable
# export DOCKER_BUILD_OPTS=--no-cache
build-cpu:
	docker build -f "./docker/t2t/Dockerfile" \
             -t $(IMG):$(TAG) \
             --label=git-versions=$(GIT_VERSION) \
             --build-arg BASE_IMAGE_TAG=$(TF_VERSION) \
             ./
	@echo Built $(IMG):$(TAG)

# TODO(jlewi): We could always use build.jsonnet and then just
# Parse out the docker build command.
build-gpu:
	docker build -f "./docker/t2t/Dockerfile" \
             -t $(IMG)-gpu:$(TAG) \
             --label=git-versions=$(GIT_VERSION) \
             --build-arg BASE_IMAGE_TAG=$(TF_VERSION)-gpu  \
             ./
	@echo Built $(IMG)-gpu:$(TAG)

build-dataflow:
	docker build -f "./docker/t2t/Dockerfile.dataflow" \
             -t $(IMG)-dataflow:$(TAG) \
             --label=git-versions=$(GIT_VERSION) \
			 .
	@echo Built $(IMG)-dataflow:$(TAG)

build: build-cpu build-gpu build-dataflow

# Build the GCB workflow
build-gcb-spec:
	rm -rf ./build
	mkdir  -p build
	jsonnet ./docker/t2t/build.jsonnet --ext-str imageBase=$(IMG) \
	  --ext-str gitVersion=$(GIT_VERSION) --ext-str tag=$(TAG) \
	  --ext-str useImageCache=$(USE_IMAGE_CACHE) \
	  > ./build/build.json
# Build using GCB. This is useful if we are on a slow internet connection
# and don't want to pull
build-gcb: build-gcb-spec	
	cp -r ./docker ./build/
	cp -r ./src ./build/
	rm -rf ./build/src/code_search/dataflow/cli/test_data
	rm -rf ./build/src/code_search/t2t/test_data
	gcloud builds submit --machine-type=n1-highcpu-32 --project=kubeflow-ci --config=./build/build.json \
		--timeout=3600 ./build

build-ui-gcb:
	rm -rf ./build
	mkdir  -p build
	jsonnet ./docker/ui/build.jsonnet --ext-str gitVersion=$(GIT_VERSION) --ext-str tag=$(TAG) \
	  > ./build/build.ui.json
	cp -r ./docker ./build/
	cp -r ./src ./build/
	rm -rf ./build/src/code_search/dataflow/cli/test_data
	rm -rf ./build/src/code_search/t2t/test_data
	gcloud builds submit --machine-type=n1-highcpu-32 --project=kubeflow-ci --config=./build/build.ui.json \
		--timeout=3600 ./build

build-ks-gcb:
	rm -rf ./build
	mkdir  -p build
	jsonnet ./docker/ks/build.jsonnet --ext-str gitVersion=$(GIT_VERSION) --ext-str tag=$(TAG) \
	  > ./build/build.ks.json
	cp -r ./docker ./build/
	cp -r ./kubeflow ./build/
	cp -r ./src ./build/
	rm -rf ./build/src/code_search/dataflow/cli/test_data
	rm -rf ./build/src/code_search/t2t/test_data
	gcloud builds submit --machine-type=n1-highcpu-32 --project=kubeflow-ci --config=./build/build.ks.json \
		--timeout=3600 ./build

# Build but don't attach the latest tag. This allows manual testing/inspection of the image
# first.
push-cpu: build-cpu
	gcloud docker --authorize-only
	docker push $(IMG):$(TAG)
	@echo Pushed $(IMG):$(TAG)

push-gpu: build-gpu
	gcloud docker --authorize-only
	docker push $(IMG)-gpu:$(TAG)
	@echo Pushed $(IMG)-gpu:$(TAG)

push-trainer: push-cpu push-gpu

push-dataflow: build-dataflow
	gcloud docker --authorize-only
	docker push $(IMG)-dataflow:$(TAG)
	@echo Pushed $(IMG)-dataflow:$(TAG)

push: push-cpu push-gpu push-dataflow
