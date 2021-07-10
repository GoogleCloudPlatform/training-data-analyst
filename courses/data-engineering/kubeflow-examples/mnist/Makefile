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
#
# To override variables do
# make ${TARGET} ${VAR}=${VALUE}
#

# IMG is the base path for images..
# Individual images will be
# $(IMG)/$(NAME):$(TAG)
IMG ?= gcr.io/kubeflow-examples/mnist

# List any changed  files. We only include files in the notebooks directory.
# because that is the code in the docker image.
CHANGED_FILES := $(shell git diff-files --relative=mnist/)

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

# Build the GCB workflow
build-gcb-spec:
	rm -rf ./build
	mkdir  -p build
	jsonnet ./image_build.jsonnet --ext-str imageBase=$(IMG) \
	  --ext-str gitVersion=$(GIT_VERSION) --ext-str tag=$(TAG) \
	  --ext-str useImageCache=$(USE_IMAGE_CACHE) \
	  > ./build/image_build.json

# Build using GCB. This is useful if we are on a slow internet connection
# and don't want to pull images locally.
# Its also used to build from our CI system.
build-gcb: build-gcb-spec		
	gcloud builds submit --machine-type=n1-highcpu-32 --project=kubeflow-ci \
	    --config=./build/image_build.json \
		--timeout=3600 .
