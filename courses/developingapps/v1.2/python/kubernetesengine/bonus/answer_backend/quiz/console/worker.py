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


from quiz.gcp import pubsub, spanner

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
- call helper module to persist to spanner
- log answer saved
"""
def answer_callback(message):
    message.ack()
    log.info('Answer received')
    log.info(message)
    data = json.loads(message.data)
    spanner.save_answer(data)
    log.info('Answer saved')   

"""
Pulls messages and loops forever while waiting
- initiate pull 
- loop once a minute, forever
"""
def main():
    log.info('Worker starting...')
    pubsub.pull_answer(answer_callback)
    while True:
        time.sleep(60)

if __name__ == '__main__':
    main()
