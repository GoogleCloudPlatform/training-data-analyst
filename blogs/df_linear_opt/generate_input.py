#!/usr/bin/env python3

import numpy as np
import json
import random
import time
import datetime

bounds = {
    'dye': (5000, 6000),
    'labor': (700, 900),
    'water': (20000, 40000),
    'concentrate': (5000, 7000)
}

N = 100
RFC3339_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S-00:00'

with open('input.json', 'w') as ofp:
    start_time = datetime.datetime.now()
    for rowno in range(N):
        data = {
            k: random.randrange(v1, v2, 10) for (k, (v1, v2)) in bounds.items()
        }
        data['timestamp'] = time.mktime((start_time + datetime.timedelta(minutes=rowno)).timetuple())
        ofp.write(json.dumps(data, ) + "\n")