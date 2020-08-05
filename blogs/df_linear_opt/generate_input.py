#!/usr/bin/env python3

import numpy as np
import json
import random

bounds = {
    'dye': (5000, 6000),
    'labor': (700, 900),
    'water': (20000, 40000),
    'concentrate': (5000, 7000)
}

N = 100

with open('input.json', 'w') as ofp:
    for i in range(N):
        data = {
            k: random.randrange(v1, v2, 10) for (k, (v1, v2)) in bounds.items()
        }
        ofp.write(json.dumps(data, ) + "\n")