from google.cloud import pubsub
from random import randint
from datetime import datetime
import json
import time


PROJECT = 'ksalama-gcp-playground'
TOPIC = 'babyweights'
TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
SAMPLE_SIZE = 5000


instances = [
      {
        'is_male': 'True',
        'mother_age': 26.0,
        'mother_race': 'Asian Indian',
        'plurality': 1.0,
        'gestation_weeks': 39,
        'mother_married': 'True',
        'cigarette_use': 'False',
        'alcohol_use': 'False'
      },
      {
        'is_male': 'False',
        'mother_age': 29.0,
        'mother_race': 'Asian Indian',
        'plurality': 1.0,
        'gestation_weeks': 38,
        'mother_married': 'True',
        'cigarette_use': 'False',
        'alcohol_use': 'False'
      },
      {
        'is_male': 'True',
        'mother_age': 26.0,
        'mother_race': 'White',
        'plurality': 1.0,
        'gestation_weeks': 39,
        'mother_married': 'True',
        'cigarette_use': 'False',
        'alcohol_use': 'False'
      },
      {
        'is_male': 'True',
        'mother_age': 26.0,
        'mother_race': 'White',
        'plurality': 2.0,
        'gestation_weeks': 37,
        'mother_married': 'True',
        'cigarette_use': 'False',
        'alcohol_use': 'True'
      }
  ]


def create_pubsub_topic():

    client = pubsub.Client(project=PROJECT)
    topic = client.topic(TOPIC)

    # if topic.exists():
    #     print('Deleting existing pub/sub topic {}...'.format(TOPIC))
    #     topic.delete()

    if not topic.exists():
        print('Creating pub/sub topic {}...'.format(TOPIC))
        topic.create()

    print('Pub/sub topic {} is up and running'.format(TOPIC))
    print("")

    return topic


def simulate_stream_data():

    topic = create_pubsub_topic()
    sleep_time = 0.05

    print("Data points to send: {}".format(SAMPLE_SIZE))
    print("PubSub topic: {}".format(TOPIC))
    print("Sleep time between each data point: {} seconds".format(sleep_time))

    for i in range(SAMPLE_SIZE):

        index = randint(0, len(instances)-1)
        instance = instances[index]

        source_timestamp = datetime.now().strftime(TIME_FORMAT)
        source_id = str(abs(hash(str(instance) + str(source_timestamp))) % (10 ** 10))

        instance['source_id'] = source_id
        instance['source_timestamp'] = source_timestamp

        message = json.dumps(instance)
        topic.publish(message=message, source_id=source_id, source_timestamp=source_timestamp)

        time.sleep(sleep_time)

        if i % 100 == 0:
            print("{} data points were sent to: {}. Last Message was: {}".format(i+1, topic.full_name, message))
            print("")

    print("Done!")


if __name__ == '__main__':
    simulate_stream_data()

