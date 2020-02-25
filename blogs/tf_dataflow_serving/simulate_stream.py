from google.cloud import pubsub
from datetime import datetime

import json
import os
import time
import argparse

MESSAGE_TIME = 0.011

PARAMS = None

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


def send_message(topic, index):

    source_timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    source_id = str(abs(hash(str(index)+str(instance)+str(source_timestamp)+str(os.getpid()))) % (10 ** 10))
    instance['source_id'] = source_id
    instance['source_timestamp'] = source_timestamp
    message = json.dumps(instance)
    topic.publish(message=message, source_id=source_id, source_timestamp=source_timestamp)
    return message


def simulate_stream_data():

    print("Data points to send: {}".format(PARAMS.stream_sample_size))
    print("PubSub topic: {}".format(PARAMS.pubsub_topic))
    print("Messages per second: {}".format(PARAMS.frequency))
    print("Sleep time between each data point: {} seconds".format(sleep_time_per_msg))

    time_start = datetime.utcnow()
    print(".......................................")
    print("Simulation started at {}".format(time_start.strftime('%Y-%m-%d %H:%M:%S')))
    print(".......................................")

    #[START simulate_stream]
    client = pubsub.Client(project=PARAMS.project_id)
    topic = client.topic(PARAMS.pubsub_topic)
    if not topic.exists():
        print 'Topic does not exist. Please run a stream pipeline first to create the topic.'
        print 'Simulation aborted.'

        return

    for index in range(PARAMS.stream_sample_size):

        message = send_message(topic, index)

        # for debugging
        if PARAMS.show_message:
            print "Message {} was sent: {}".format(index+1, message)
            print ""

        time.sleep(sleep_time_per_msg)
    #[END simulate_stream]

    time_end = datetime.utcnow()

    print(".......................................")
    print("Simulation finished at {}".format(time_end.strftime('%Y-%m-%d %H:%M:%S')))
    print(".......................................")
    time_elapsed = time_end - time_start
    time_elapsed_seconds = time_elapsed.total_seconds()
    print("Simulation elapsed time: {} seconds".format(time_elapsed_seconds))
    print("{} data points were sent to: {}.".format(PARAMS.stream_sample_size, topic.full_name))
    print("Average frequency: {} per second".format(round(PARAMS.stream_sample_size/time_elapsed_seconds, 2)))


if __name__ == '__main__':

    args_parser = argparse.ArgumentParser()

    args_parser.add_argument(
        '--project_id',
        help="""
        Google Cloud project id\
        """,
        default='ksalama-gcp-playground',
    )

    args_parser.add_argument(
        '--pubsub-topic',
        help="""
        Cloud Pub/Sub topic to send the messages to\
        """,
        default='babyweights',
    )

    args_parser.add_argument(
        '--frequency',
        help="""
        Number of messages per seconds to be sent to the topic in streaming pipelines\
        """,
        default=50,
        type=int
    )

    args_parser.add_argument(
        '--stream-sample-size',
        help="""
        Total number of messages be sent to the topic in streaming pipelines\
        """,
        default=10,
        type=int
    )

    args_parser.add_argument(
        '--show-message',
        action='store_true',
        default=False
    )

    PARAMS = args_parser.parse_args()

    print ''
    print 'Simulation Parameters:'
    print PARAMS
    print ''

    total_msg_time = MESSAGE_TIME * PARAMS.frequency  # time to send the required messages per second
    total_sleep_time = 1 - total_msg_time  # total sleep time per second (in order not to send more)
    sleep_time_per_msg = total_sleep_time / PARAMS.frequency

    simulate_stream_data()

