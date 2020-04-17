# This program reads a file representing web server logs in common log format and streams them into a PubSub topic
# with lag characteristics as determined by command-line arguments

import argparse
from google.cloud import pubsub_v1
import time
from datetime import datetime, timezone
import random
from anytree.importer import DictImporter
import json
from multiprocessing import Process

parser = argparse.ArgumentParser(__file__, description="event_generator")
parser.add_argument("--taxonomy", "-x", dest="taxonomy_fp",
                    help="A .json file representing a taxonomy of web resources",
                    default="taxonomy.json")
parser.add_argument("--users_fp", "-u", dest="users_fp",
                    help="A .csv file of users",
                    default="users.csv")
parser.add_argument("--off_to_on", "-off", dest="off_to_on_prob", type=float,
                    help="A float representing the probability that a user who is offline will come online",
                    default=.25)
parser.add_argument("--on_to_off", "-on", dest="on_to_off_prob", type=float,
                    help="A float representing the probability that a user who is online will go offline",
                    default=.1)
parser.add_argument("--max_lag_millis", '-l', dest="max_lag_millis", type=int,
                    help="An integer representing the maximum amount of lag in millisecond", default=250)
parser.add_argument("--project_id", "-p", type=str, dest="project_id", help="A GCP Project ID", required=True)
parser.add_argument("--topic_name", "-t", dest="topic_name", type=str,
                    help="The name of the topic where the messages to be published", required=True)


avg_secs_between_events = 5
args = parser.parse_args()
taxonomy_fp = args.taxonomy_fp
users_fp = args.users_fp
online_to_offline_probability = args.on_to_off_prob
offline_to_online_probability = args.off_to_on_prob
max_lag_millis = args.max_lag_millis
project_id = args.project_id
topic_name = args.topic_name
min_file_size_bytes = 100
max_file_size_bytes = 500
verbs = ["GET"]
responses = [200]


log_fields = ["ip", "user_id", "lat", "lng", "timestamp", "http_request",
              "http_response", "num_bytes", "user_agent"]

def extract_resources(taxonomy_filepath):
    """
    Reads a .json representing a taxonomy and returns
    a data structure representing their hierarchical relationship
    :param taxonomy_file: a string representing a path to a .json file
    :return: Node representing root of taxonomic tree
    """

    try:
        with open(taxonomy_filepath, 'r') as fp:
            json_str = fp.read()
            json_data = json.loads(json_str)
            root = DictImporter().import_(json_data)
    finally:
        fp.close()

    return root


def read_users(users_fp):
    """
    Reads a .csv from @user_fp representing users into a list of dictionaries,
    each elt of which represents a user
    :param user_fp: a .csv file where each line represents a user
    :return: a list of dictionaries
    """
    users = []
    with open(users_fp, 'r') as fp:
        fields = fp.readline().rstrip().split(",")
        for line in fp:
            user = dict(zip(fields, line.rstrip().split(",")))
            users.append(user)
    return users

def sleep_then_publish_burst(burst, publisher, topic_path):
    """

    :param burst: a list of dictionaries, each representing an event
    :param num_events_counter: an instance of Value shared by all processes
    to track the number of published events
    :param publisher: a PubSub publisher
    :param topic_path: a topic path for PubSub
    :return:
    """
    sleep_secs = random.uniform(0, max_lag_millis/1000)
    time.sleep(sleep_secs)
    publish_burst(burst, publisher, topic_path)

def publish_burst(burst, publisher, topic_path):
    """
    Publishes and prints each event
    :param burst: a list of dictionaries, each representing an event
    :param num_events_counter: an instance of Value shared by all processes to
    track the number of published events
    :param publisher: a PubSub publisher
    :param topic_path: a topic path for PubSub
    :return:
    """
    for event_dict in burst:
        json_str = json.dumps(event_dict)
        data = json_str.encode('utf-8')
        publisher.publish(topic_path, data=data, timestamp=event_dict['timestamp'])

def create_user_process(user, root):
    """
    Code for continuously-running process representing a user publishing
    events to pubsub
    :param user: a dictionary representing characteristics of the user
    :param root: an instance of AnyNode representing the home page of a website
    :param num_events_counter: a variable shared among all processes used to track the number of events published
    :return:
    """
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_name)

    user['page'] = root
    user['is_online'] = True
    user['offline_events'] = []

    while True:
        time_between_events = random.uniform(0, avg_secs_between_events * 2)
        time.sleep(time_between_events)
        prob = random.random()
        event = generate_event(user)
        if user['is_online']:
            if prob < online_to_offline_probability:
                user['is_online'] = False
                user['offline_events'] = [event]
            else:
                sleep_then_publish_burst([event], publisher, topic_path)
        else:
            user['offline_events'].append(event)
            if prob < offline_to_online_probability:
                user['is_online'] = True
                sleep_then_publish_burst(user['offline_events'], publisher, topic_path)
                user['offline_events'] = []

def generate_event(user):
    """
    Returns a dictionary representing an event
    :param user:
    :return:
    """
    user['page'] = get_next_page(user)
    uri = str(user['page'].name)
    event_time = datetime.now(tz=timezone.utc)
    current_time_str = event_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    file_size_bytes = random.choice(range(min_file_size_bytes, max_file_size_bytes))
    http_request = "\"{} {} HTTP/1.0\"".format(random.choice(verbs), uri)
    http_response = random.choice(responses)
    event_values = [user['ip'], user['id'], float(user['lat']), float(user['lng']), current_time_str, http_request,
                    http_response, file_size_bytes, user['user_agent']]

    return dict(zip(log_fields, event_values))

def get_next_page(user):
    """
    Consults the user's representation of the web site taxonomy to determine the next page that they visit
    :param user:
    :return:
    """
    possible_next_pages = [user['page']]
    if not user['page'].is_leaf:
        possible_next_pages += list(user['page'].children)
    if (user['page'].parent != None):
        possible_next_pages += [user['page'].parent]
    next_page = random.choice(possible_next_pages)
    return next_page


if __name__ == '__main__':
    users = read_users(users_fp)
    root = extract_resources(taxonomy_fp)
    processes = [Process(target=create_user_process, args=(user, root))
                 for user in users]
    [process.start() for process in processes]
    while True:
        time.sleep(1)