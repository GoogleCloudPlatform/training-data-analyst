#!/bin/bash

# Script to set up necessary packages and run tweet-gatherer script.
# User needs to update TODOs starting on line 10.

apt-get install -y python-pip
pip install tweepy
pip install google-cloud-pubsub

python tweets-gatherer.py \
    --project_name maabel-testground \
    --topic_name tweet-nlp-demo \
    --tw_consumer_key #TODO: ADD TWITTER API CONSUMER KEY  \
    --tw_consumer_sec #TODO: ADD TWITTER API CONSUMER SECRET   \
    --tw_acc_token #TODO: ADD TWITTER API ACCESS KEY  \
    --tw_acc_sec #TODO: ADD TWITTER API ACCESS SECRET  \
    --no_tweets 10000 \
    --search_term pizza \
