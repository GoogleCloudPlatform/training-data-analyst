#!/bin/bash

# Copyright 2020 Google Inc. All Rights Reserved.
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


# Script to set up necessary packages and run tweet-gatherer script.
# User needs to update TODOs starting on line 29.

apt-get install -y python-pip
pip install tweepy
pip install google-cloud-pubsub

gcloud pubsub topics create tweet-nlp-demo
bq mk -d tweet_nlp_demo

python tweets-gatherer.py \
    --project_name #TODO: ADD YOUR PROJECT NAME \
    --topic_name tweet-nlp-demo \
    --tw_consumer_key #TODO: ADD TWITTER API CONSUMER KEY  \
    --tw_consumer_sec #TODO: ADD TWITTER API CONSUMER SECRET   \
    --tw_acc_token #TODO: ADD TWITTER API ACCESS KEY  \
    --tw_acc_sec #TODO: ADD TWITTER API ACCESS SECRET  \
    --no_tweets 10000 \
    --search_term pizza \
