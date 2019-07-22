from google.cloud import pubsub


TOPIC = 'babyweights'
SUBSCRIPTION='babyweights-sub'

client = pubsub.Client()
topic = client.topic(TOPIC)

subscription = topic.subscription(name=SUBSCRIPTION)
if not subscription.exists():
    print('Creating pub/sub subscription {}...'.format(SUBSCRIPTION))
    subscription.create(client=client)

print ('Pub/sub subscription {} is up and running'.format(SUBSCRIPTION))
print("")


subscription = topic.subscription(SUBSCRIPTION)
message = subscription.pull(return_immediately=True)

print("source_id", message[0][1].attributes["source_id"])
print("source_timestamp:", message[0][1].attributes["source_timestamp"])
print("")
print(message[0][1].data)

