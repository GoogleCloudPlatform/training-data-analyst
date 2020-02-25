from sys import path
from os.path import dirname as dir

path.append(dir(path[0]))
__package__ = "model"

from model import inference
from datetime import datetime


INFERENCE_TYPE = 'local'  # local' | 'cmle'

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
        'is_male': 'True',
        'mother_age': 26.0,
        'mother_race': 'Asian Indian',
        'plurality': 1.0,
        'gestation_weeks': 39,
        'mother_married': 'True',
        'cigarette_use': 'False',
        'alcohol_use': 'False'
      }
]

print("")
print("Inference Type:{}".format(INFERENCE_TYPE))
print("")

time_start = datetime.utcnow()
print("Inference started at {}".format(time_start.strftime("%H:%M:%S")))
print(".......................................")


for i in range(10):
    if INFERENCE_TYPE == 'local':
        output = inference.estimate_local(instances)
    else:
        output = inference.estimate_cmle(instances)
    print(output)

time_end = datetime.utcnow()
print(".......................................")
print("Inference finished at {}".format(time_end.strftime("%H:%M:%S")))
print("")
time_elapsed = time_end - time_start
print("Inference elapsed time: {} seconds".format(time_elapsed.total_seconds()))
