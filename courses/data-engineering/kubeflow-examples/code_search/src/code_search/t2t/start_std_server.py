import json
import logging
import os
import tensorflow as tf

if __name__ == '__main__':
  logging.basicConfig(level=logging.INFO,
                      format=('%(levelname)s|%(asctime)s'
                              '|%(pathname)s|%(lineno)d| %(message)s'),
                      datefmt='%Y-%m-%dT%H:%M:%S',
                      )
  logging.getLogger().setLevel(logging.INFO)
  tf_config = os.environ.get('TF_CONFIG', '{}')
  logging.info("TF_CONFIG %s", tf_config)
  tf_config_json = json.loads(tf_config)

  cluster = tf_config_json.get('cluster')
  job_name = tf_config_json.get('task', {}).get('type')
  task_index = tf_config_json.get('task', {}).get('index')
  logging.info("cluster=%s job_name=%s task_index=%s", cluster, job_name,
               task_index)

  logging.info("Starting stdandrd server.")
  cluster_spec = tf.train.ClusterSpec(cluster)
  server = tf.train.Server(cluster_spec, job_name=job_name, task_index=task_index)
  server.join()
