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
# Requirements:
#   https://github.com/mattrobenolt/jinja2-cli
#   pip install jinja2-clie
# Update the Airflow deployment

# List any changed  files. We only include files in the notebooks directory.
# because that is the code in the docker image.
# In particular we exclude changes to the ksonnet configs.
CHANGED_FILES := $(shell git diff-files --relative=github_issue_summarization/notebooks)

ifeq ($(strip $(CHANGED_FILES)),)
# Changed files is empty; not dirty
# Don't include --dirty because it could be dirty if files outside the ones we care
# about changed.
GIT_VERSION := $(shell git describe --always)
else
GIT_VERSION := $(shell git describe --always)-dirty-$(shell git diff | shasum -a256 | cut -c -6)
endif

TAG := $(shell date +v%Y%m%d)-$(GIT_VERSION)

DIR := $(shell pwd)

# Use a subdirectory of the root directory
# this way it will be excluded by git diff-files
BUILD_DIR := $(shell pwd)/build

MODEL_GCS := gs://kubeflow-examples-data/gh_issue_summarization/model/v20180426
# You can override this on the command line as
# make PROJECT=kubeflow-examples <target>
PROJECT := kubeflow-examples

IMG := gcr.io/$(PROJECT)/tf-job-issue-summarization
IMG_ESTIMATOR := gcr.io/$(PROJECT)/tf-job-issue-summarization-estimator

# gcr.io is prepended automatically by Seldon's builder.
MODEL_IMG_NAME := $(PROJECT)/issue-summarization-model
MODEL_IMG := gcr.io/$(MODEL_IMG_NAME)

echo:
	@echo changed files $(CHANGED_FILES)
	@echo tag $(TAG)
	@echo BUILD_DIR=$(BUILD_DIR)

push: build
	gcloud docker -- push $(IMG):$(TAG)

set-image: push
	# Set the image to use
	cd ../ks_app && ks param set tfjob-pvc image $(IMG):$(TAG)

# To build without the cache set the environment variable
# export DOCKER_BUILD_OPTS=--no-cache
build:
	docker build ${DOCKER_BUILD_OPTS} -f Dockerfile -t $(IMG):$(TAG) ./
	@echo Built $(IMG):$(TAG)

$(BUILD_DIR)/body_pp.dpkl:
	mkdir -p $(BUILD_DIR)
	gsutil cp $(MODEL_GCS)/body_pp.dpkl $(BUILD_DIR)/

$(BUILD_DIR)/title_pp.dpkl:
	mkdir -p $(BUILD_DIR)
	gsutil cp $(MODEL_GCS)/title_pp.dpkl $(BUILD_DIR)/

$(BUILD_DIR)/seq2seq_model_tutorial.h5:
	mkdir -p $(BUILD_DIR)
	gsutil cp $(MODEL_GCS)/seq2seq_model_tutorial.h5 $(BUILD_DIR)/

# Copy python files into the model directory
# so that we can mount a single directory into the container
$(BUILD_DIR)/% : %
	mkdir -p $(BUILD_DIR)
	cp -f $< $@

download-model:	$(BUILD_DIR)/seq2seq_model_tutorial.h5 $(BUILD_DIR)/title_pp.dpkl $(BUILD_DIR)/body_pp.dpkl

build-model-image: download-model $(BUILD_DIR)/seq2seq_utils.py $(BUILD_DIR)/IssueSummarization.py $(BUILD_DIR)/requirements.txt $(BUILD_DIR)/environment_seldon_rest
	cd $(BUILD_DIR) && s2i build -E environment_seldon_rest . seldonio/seldon-core-s2i-python36:0.4 $(MODEL_IMG):$(TAG)
	@echo built $(MODEL_IMG):$(TAG)

start-docker-model-image:
	docker run --name "issue-model" -d --rm -p 5000:5000 $(MODEL_IMG):$(TAG)

stop-docker-model-image:
	docker rm -f issue-model

test-model-image_local:
	curl -g http://localhost:5000/predict --data-urlencode 'json={"data":{"ndarray":[["try to stop flask from using multiple threads"]]}}'

push-model-image: 
	echo pushing $(MODEL_IMG):$(TAG)
	gcloud docker -- push $(MODEL_IMG):$(TAG)

set-model-image: push-model-image
	# Set the image to use
	cd ../ks_app && ks param set issue-summarization-model image $(MODEL_IMG):$(TAG)

# Build the estimator image
build-estimator:
	cd .. && docker build ${DOCKER_BUILD_OPTS} -t $(IMG_ESTIMATOR):$(TAG) . \
					-f ./notebooks/Dockerfile.estimator --label=git-verions=$(GIT_VERSION)
	@echo Built $(IMG_ESTIMATOR):$(TAG)

push-estimator: build-estimator
	gcloud docker -- push $(IMG_ESTIMATOR):$(TAG)
	@echo Pushed $(IMG_ESTIMATOR):$(TAG)

.PHONY: clean
clean:
	rm -rf build
