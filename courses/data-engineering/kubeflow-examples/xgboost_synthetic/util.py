import os
import json
import shutil
import requests

from retrying import retry
import numpy as np

def copy_data_to_nfs(nfs_path, model_dir):
  if not os.path.exists(nfs_path):
    shutil.copytree("ames_dataset", nfs_path)

  if not os.path.exists(model_dir):
    os.makedirs(model_dir)

@retry(wait_exponential_multiplier=1000, wait_exponential_max=5000,
       stop_max_delay=2*60*1000)
def predict_nparray(url, data, feature_names=None):
  pdata = {
      "data": {
          "names":feature_names,
          "tensor": {
              "shape": np.asarray(data.shape).tolist(),
              "values": data.flatten().tolist(),
          },
      }
  }
  serialized_data = json.dumps(pdata)
  r = requests.post(url, data={'json':serialized_data}, timeout=5)
  return r
