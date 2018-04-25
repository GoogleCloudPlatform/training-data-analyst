from google.cloud import pubsub
from random import randint
from datetime import datetime
import json


PROJECT = 'ksalama-gcp-playground'
TOPIC = 'babyweights'
TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
SAMPLE_SIZE = 100
#MESSAGES_PER_SEC = 50


instance = {
        'is_male': 'True',
        'mother_age': 26.0,
        'mother_race': 'Asian Indian',
        'plurality': 1.0,
        'gestation_weeks': 39,
        'mother_married': 'True',
        'cigarette_use': 'False',
        'alcohol_use': 'False'
      }


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
    # sleep_time = 1.0/MESSAGES_PER_SEC

    print("Data points to send: {}".format(SAMPLE_SIZE))
    print("PubSub topic: {}".format(TOPIC))
    # print("Messages per second: {}".format(MESSAGES_PER_SEC))
    # print("Sleep time between each data point: {} seconds".format(sleep_time))

    def _send_message():

        source_timestamp = datetime.utcnow().strftime(TIME_FORMAT)
        source_id = str(abs(hash(str(instance) + str(source_timestamp))) % (10 ** 10))

        instance['source_id'] = source_id
        instance['source_timestamp'] = source_timestamp

        message = json.dumps(instance)

        topic.publish(message=message, source_id=source_id, source_timestamp=source_timestamp)

    time_start = datetime.utcnow()
    print(".......................................")
    print("Simulation started at {}".format(time_start.strftime("%H:%M:%S")))
    print(".......................................")

    for i in range(SAMPLE_SIZE):

        _send_message()

        # time.sleep(sleep_time)

        # if (i+1) % 10 == 0:
        #     print("{} data points were sent to: {}.".format(i+1, topic.full_name))
        #     print()
        #     print("")

    time_end = datetime.utcnow()

    print(".......................................")
    print("Simulation finished at {}".format(time_end.strftime("%H:%M:%S")))
    print(".......................................")
    time_elapsed = time_end - time_start
    print("Simulation elapsed time: {} seconds".format(time_elapsed.total_seconds()))
    print("Average frequency: {} per second".format(round(SAMPLE_SIZE/time_elapsed.total_seconds(), 2)))


if __name__ == '__main__':
    simulate_stream_data()

