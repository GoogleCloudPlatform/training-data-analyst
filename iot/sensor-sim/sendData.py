import argparse
import concurrent.futures
import time

#from google.cloud import pubsub_v1

def publish_messages(project, topic_name):
    """Publishes multiple messages to a Pub/Sub topic."""
    # [START pubsub_quickstart_publisher]
    # [START pubsub_publish]
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project, topic_name)
    f = open("sensorData.txt","r")

    #for n in range(1, 10):
    while True:
        #data = u'Message number {}'.format(n)
        data=f.readline()
        if data == '':
            break
        else:
            # Data must be a bytestring
            data = data.encode('utf-8')
            publisher.publish(topic_path, data=data)
            print(data)
            time.sleep(30)
    print('Published messages.')
    # [END pubsub_quickstart_publisher]
    # [END pubsub_publish]

ap=argparse.ArgumentParser()
ap.add_argument("-p","--project", required=True)
ap.add_argument("-t","--topic_name", required=True)
args=vars(ap.parse_args())

publish_messages(args["project"], args["topic_name"])
