# Copyright 2017 Google Inc.
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

import logging
import sys
import time
import json

# TODO: Load the pubsub, languageapi and spanner modules from the quiz.gcp package



# END TODO

"""
Configure logging
"""
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
log = logging.getLogger()

"""
Receives pulled messages, analyzes and stores them
- Acknowledge the message
- Log receipt and contents
- convert json string
- call helper module to do sentiment analysis
- log sentiment score
- call helper module to persist to spanner
- log feedback saved
"""
def pubsub_callback(message):
    data = json.loads(message.data)

     

    # TODO: Acknowledge the message

    

    # END TODO

    

    # TODO: Log the message

    

    # END TODO

    

    # TODO: Use the languageapi module to analyze the sentiment

    

    # END TODO

    # TODO: Log the sentiment score

    

    # END TODO

    # TODO: Assign the sentiment score to a new score property

    

    # END TODO

    # TODO: Use the spanner module to save the feedback

    

    # END TODO 

    # TODO: Log a message to say the feedback has been saved

        

    # END TODO

"""
Pulls messages and loops forever while waiting
- initiate pull 
- loop once a minute, forever
"""
def main():
    log.info('Worker starting...')

    # TODO: Register the callback

    

    # END TODO

    while True:
        time.sleep(60)

if __name__ == '__main__':
    main()
