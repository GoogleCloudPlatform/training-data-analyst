# demo of message pull with pubsub
# make sure you have pubsub installed. On cloud shell you can just run
# sudo pip install --upgrade google-cloud-pubsub
#
# you will also need to create a topic and subscription. From cloud shell
# gcloud pubsub topics create cp300
# gcloud pubsub subscriptions create cpsubs --topic=cp300

from google.cloud import pubsub_v1

subscriber = pubsub_v1.SubscriberClient()

def callback(message):
  print('Received message: {}'.format(message))
  message.ack()

# make sure you replace "javier" with your project name 
subscription_path = 'projects/javier/subscriptions/cpsubs'
subscriber.subscribe(subscription_path, callback=callback)

# just go to https://console.cloud.google.com/cloudpubsub/subscriptions/cpsubs
# and publish some messages. You will see the payload inmediately on cloudshell
#
# note even if we are pulling behind the scenes, the client libraries are designed so from the developer's point of view 
# it works like a push. You just register a callback and forget. No need to keep looping and pulling and sleeping
