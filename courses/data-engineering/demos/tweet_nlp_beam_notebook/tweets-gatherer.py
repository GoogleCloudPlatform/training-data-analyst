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

"""
A python script to pull tweets about Google from via the Twitter API
and publish them to a specified Pub/Sub topic.

Use the tweet-setup.sh script to install packages on your VM and run this script.

USAGE:
python tweets-gatherer.py \
    --project_name [...] \
    --topic_name [...] \
    --tw_consumer_key [...] \
    --tw_consumer_sec [...] \
    --tw_acc_token [...] \
    --tw_acc_sec [...] \
    --no_tweets [...] \
    --search_term [...] \
"""

import tweepy, json, datetime, argparse
from google.cloud import pubsub

parser = argparse.ArgumentParser()
# Required Arguments
parser.add_argument('--project_name', required=True, help=('GCP project name'))
parser.add_argument('--topic_name', required = True, help=('Pub/Sub topic'))
parser.add_argument('--tw_consumer_key', required = True, help=('Twitter Consumer Key'))
parser.add_argument('--tw_consumer_sec', required = True, help= ('Twitter Consumer Secret'))
parser.add_argument('--tw_acc_token', required = True, help = ('Twitter Access Token'))
parser.add_argument('--tw_acc_sec', required = True, help = ('Twitter Secret Token'))
parser.add_argument('--search_term', action='append', required = True,
                    default = [], help=('Search term for tweets'))
                    # Currently code only supports single search term!

# Optional Arguments
parser.add_argument('--no_tweets', default = 10000, help=('Number of tweets to be processed'))

"""
Define global variables for this script.
"""

args = parser.parse_args()

GCP_PROJECT_NAME = args.project_name
PUBSUB_TOPIC_NAME = args.topic_name
TOTAL_TWEETS = int(args.no_tweets)

TWITTER_CONSUMER_KEY = args.tw_consumer_key
TWITTER_CONSUMER_SECRET = args.tw_consumer_sec
TWITTER_ACCESS_TOKEN = args.tw_acc_token
TWITTER_ACCESS_TOKEN_SECRET = args.tw_acc_sec

SEARCH_TERM = args.search_term

"""
Define a function to publish to the Pub/Sub topic.
"""
def publish(client, pubsub_topic, data_lines):
    messages = []
    for line in data_lines:
        messages.append({'data': line})
    body = {'messages': messages}
    str_body = json.dumps(body, ensure_ascii=False) # Encode the data from Twitter API as a JSON object.
    data = str_body.encode(encoding='UTF-8') # Encode the JSON object using UTF-8.

    client.publish(topic=pubsub_topic, data=data)


class TweetStreamListener(tweepy.StreamListener):
    """
    A listener handles tweets that are received from the stream.
    This listener dumps the tweets into a Pub/Sub topic.
    """
    client = pubsub.PublisherClient()
    pubsub_topic = client.topic_path(GCP_PROJECT_NAME, PUBSUB_TOPIC_NAME)
    count = 0
    tweets = []
    batch_size = 1 #process-tweets.py file set up to handle one tweet at a time!
    total_tweets = TOTAL_TWEETS

    def write_to_pubsub(self, tweets):
        publish(self.client, self.pubsub_topic, tweets)

    def on_status(self, status):

        created_at = status.created_at.isoformat()
        id_str = status.id_str
        text = status.text
        source = status.source
        user_name = status.user.name
        user_screen_name = status.user.screen_name
        loc = status.user.location
        coords = status.coordinates
        lang = status.user.lang
        bio = status.user.description

        tw = dict(text=text, bio=bio, created_at=created_at, tweet_id=id_str,
                  location=loc, user_name=user_name,
                  user_screen_name=user_screen_name,
                  source=source, coords=coords, lang=lang)

        self.tweets.append(tw)

        if len(self.tweets) >= self.batch_size:
            self.write_to_pubsub(self.tweets)
            # print(self.tweets) # <- For debugging
            self.tweets = []

        self.count += 1
        if self.count >= self.total_tweets:
            return False
        if (self.count % 100) == 0:
            print("count is: {} at {}".format(self.count, datetime.datetime.now()))
            # Status message every 100 tweets.
        return True

    def on_error(self, status_code):
        print('ERROR:{}'.format(status_code))
        # To handle possble errors from the Twitter API


if __name__ == '__main__':

    print('Initialize tweet gathering for tweets related to {}.'.format(SEARCH_TERM))

    auth = tweepy.OAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
    auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)

    stream_listener = TweetStreamListener()
    stream = tweepy.Stream(auth, stream_listener)

    stream.filter(
        track=SEARCH_TERM
    )
