# Copyright 2017 The Kubernetes Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
# Environment variable project must be set.
#
TAG := $(shell date +v%Y%m%d)-$(shell git describe --tags --always --dirty)-$(shell git diff | shasum -a256 | cut -c -6)
DIR := ${CURDIR}

# You can override this on the command line as
# make PROJECT=kf-internal-dev <target>

ifndef PROJECT
$(error PROJECT is not set)
endif

ifndef ENV
$(error ENV is not set)
endif

# TPU uses the same docker image as CPU .
CPU_IMG := gcr.io/$(PROJECT)/kubeflow-yelp-demo-cpu
GPU_IMG := gcr.io/$(PROJECT)/kubeflow-yelp-demo-gpu
UI_IMG  := gcr.io/$(PROJECT)/kubeflow-yelp-demo-ui

# The tag refered to in the README.md
VERSION_TAG := 1.0

echo:
	@echo PROJECT=${PROJECT}
	@echo ENV=${ENV}
	@echo CPU_IMG=${CPU_IMG}
	@echo GPU_IMG=${GPU_IMG}
	@echo UI_IMG=${UI_IMG}

all: build push set-image

push: push-cpu push-gpu push-ui

push-gpu: build-gpu
	gcloud docker -- push $(GPU_IMG):latest
	gcloud docker -- push $(GPU_IMG):$(TAG)
	gcloud docker -- push $(GPU_IMG):$(VERSION_TAG)

push-cpu: build-cpu
	gcloud docker -- push $(CPU_IMG):latest
	gcloud docker -- push $(CPU_IMG):$(TAG)
	gcloud docker -- push $(CPU_IMG):$(VERSION_TAG)

push-ui: build-ui
	gcloud docker -- push $(UI_IMG):latest
	gcloud docker -- push $(UI_IMG):$(TAG)
	gcloud docker -- push $(UI_IMG):$(VERSION_TAG)

set-image: set-image-cpu set-image-gpu set-image-ui

set-image-cpu: push-cpu
	cd demo && ks param set --env=$(ENV) t2tcpu cpuImage $(CPU_IMG):$(TAG)
	cd demo && ks param set --env=$(ENV) t2ttpu cpuImage $(CPU_IMG):$(TAG)

set-image-gpu: push-gpu
	cd demo && ks param set --env=$(ENV) t2tgpu gpuImage $(GPU_IMG):$(TAG)
	cd demo && ks param set --env=$(ENV) t2ttpu gpuImage $(GPU_IMG):$(TAG)

set-image-ui: push-ui
	cd demo && ks param set --env=$(ENV) ui image $(UI_IMG):$(TAG)

# To build without the cache set the environment variable
# export DOCKER_BUILD_OPTS=--no-cache
build: build-cpu build-gpu build-ui

build-cpu:
	docker build ${DOCKER_BUILD_OPTS} --build-arg BASE_IMAGE=gcr.io/kubeflow-images-public/tensorflow-1.7.0-notebook-cpu:latest -f Dockerfile.training -t $(CPU_IMG):$(TAG) ./yelp/yelp_sentiment
	docker tag $(CPU_IMG):$(TAG) $(CPU_IMG):latest
	docker tag $(CPU_IMG):$(TAG) $(CPU_IMG):$(VERSION_TAG)
	@echo Built $(CPU_IMG):$(TAG) and tagged with latest

build-gpu:
	docker build ${DOCKER_BUILD_OPTS} --build-arg BASE_IMAGE=gcr.io/kubeflow-images-public/tensorflow-1.7.0-notebook-gpu:latest -f  Dockerfile.training -t $(GPU_IMG):$(TAG) ./yelp/yelp_sentiment
	docker tag $(GPU_IMG):$(TAG) $(GPU_IMG):latest
	docker tag $(GPU_IMG):$(TAG) $(GPU_IMG):$(VERSION_TAG)
	@echo Built $(GPU_IMG):$(TAG) and tagged with latest

build-ui:
	docker build ${DOCKER_BUILD_OPTS} -f Dockerfile.ui -t $(UI_IMG):$(TAG) .
	docker tag $(UI_IMG):$(TAG) $(UI_IMG):latest
	docker tag $(UI_IMG):$(TAG) $(UI_IMG):$(VERSION_TAG)
	@echo Built $(UI_IMG):$(TAG) and tagged with latest


