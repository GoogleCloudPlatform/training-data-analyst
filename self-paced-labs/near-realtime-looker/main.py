import base64
import json
import os
import random
from datetime import datetime
from google.cloud import pubsub_v1                                

publisher_client = pubsub_v1.PublisherClient()
PROJECT_ID = 'firstproj-373812' # GOOGLE_CLOUD_PROJECT <please update your google cloud project id>
topic_id = 'city-sensor-temp'                                


def createjson(city:str , base_temp:float, base_pressure:int):
    city = city
    temperature = round(base_temp + random.uniform(0.0, 1.0),2)
    pressure = base_pressure + random.randint(1, 4)
    now = datetime.now()
    time_position = now.strftime("%Y-%m-%d %H:%M:%S")
    message_json = json.dumps({
            'city': city,
            'temperature': temperature,
            'pressure': pressure,
            'time_position': time_position 
    })
    return str(message_json)

def publisher_function(request):
    json_list = []
    pune_json = createjson('Pune',20.00,80)
    ny_json = createjson('New York',3.00,50)
    lon_json = createjson('London',10.00,40)
    bris_json = createjson('Brisbane',25.00,100)
    cch_json = createjson('Christchurch',15.00,120)
    json_list = [pune_json , ny_json,lon_json,bris_json,cch_json]
    

    ###############################
    # move the data to Pubsub!

    topic_path = publisher_client.topic_path(PROJECT_ID, topic_id)                    # Pubsub topic path

    for message_json in json_list:
        message_encode = message_json.encode('utf-8')
        try:
            publish_data = publisher_client.publish(topic_path, data=message_encode)
            publish_data.result() 
        except Exception as e:   
            print(e) 
            return (e, 500)

    return ('Message published to Pubsub', 200)
