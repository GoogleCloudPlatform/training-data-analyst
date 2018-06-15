# Copyright 2018 Google Inc. All Rights Reserved.
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

import argparse
import datetime
import tensorflow as tf
import apache_beam as beam
import shutil, os, subprocess, sys

# code from https://raw.githubusercontent.com/tensorflow/tpu/master/tools/datasets/imagenet_to_gcs.py
def _int64_feature(value):
  """Wrapper for inserting int64 features into Example proto."""
  if not isinstance(value, list):
    value = [value]
  return tf.train.Feature(int64_list=tf.train.Int64List(value=value))

def _bytes_feature(value):
  """Wrapper for inserting bytes features into Example proto."""
  return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))

def _convert_to_example(filename, image_buffer, label_int, label_str, height, width):
  """Build an Example proto for an example.

  Args:
    filename: string, path to an image file, e.g., '/path/to/example.JPG'
    image_buffer: string, JPEG encoding of RGB image
    label_int: integer, identifier for the ground truth for the network (0-based)
    label_str: string, identifier for the ground truth for the network, e.g., 'daisy'
    height: integer, image height in pixels
    width: integer, image width in pixels
  Returns:
    Example proto
  """
  colorspace = 'RGB'
  channels = 3
  image_format = 'JPEG'

  example = tf.train.Example(features=tf.train.Features(feature={
      'image/height': _int64_feature(height),
      'image/width': _int64_feature(width),
      'image/colorspace': _bytes_feature(colorspace),
      'image/channels': _int64_feature(channels),
      'image/class/label': _int64_feature(label_int+1), # model expects 1-based
      'image/class/synset': _bytes_feature(label_str),
      'image/format': _bytes_feature(image_format),
      'image/filename': _bytes_feature(os.path.basename(filename)),
      'image/encoded': _bytes_feature(image_buffer)}))
  return example

class ImageCoder(object):
  """Helper class that provides TensorFlow image coding utilities."""

  def __init__(self):
    # Create a single Session to run all image coding calls.
    self._sess = tf.Session()
    
    # Initializes function that decodes RGB JPEG data.
    self._decode_jpeg_data = tf.placeholder(dtype=tf.string)
    self._decode_jpeg = tf.image.decode_jpeg(self._decode_jpeg_data, channels=3)

  def decode_jpeg(self, image_data):
    image = self._sess.run(self._decode_jpeg,
                           feed_dict={self._decode_jpeg_data: image_data})
    assert len(image.shape) == 3
    assert image.shape[2] == 3
    return image
  
  def __del__(self):
    self._sess.close()
  
def _get_image_data(filename, coder):
  """Process a single image file.

  Args:
    filename: string, path to an image file e.g., '/path/to/example.JPG'.
    coder: instance of ImageCoder to provide TensorFlow image coding utils.
  Returns:
    image_buffer: string, JPEG encoding of RGB image.
    height: integer, image height in pixels.
    width: integer, image width in pixels.
  """
  # Read the image file.
  with tf.gfile.FastGFile(filename, 'r') as f:
    image_data = f.read()

  # Decode the RGB JPEG.
  image = coder.decode_jpeg(image_data)

  # Check that image converted to RGB
  assert len(image.shape) == 3
  height = image.shape[0]
  width = image.shape[1]
  assert image.shape[2] == 3

  return image_data, height, width

def convert_to_example(line, categories):
    filename, label = line.encode('ascii','ignore').split(',') # read from inputCsv
    if label in categories:
       # ignore labels not in categories list
       coder = ImageCoder()
       image_buffer, height, width = _get_image_data(filename, coder)
       del coder
       example = _convert_to_example(filename, image_buffer, categories.index(label), label, height, width)
       yield example.SerializeToString()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--trainCsv',
        help = 'Path to input.  Each line of input has two fields  image-file-name and label separated by a comma',
        required = True
    )
    parser.add_argument(
        '--validationCsv',
        help = 'Path to input.  Each line of input has two fields  image-file-name and label separated by a comma',
        required = True
    )
    parser.add_argument(
        '--labelsFile',
        help = 'Path to file containing list of labels, one per line',
        required = True
    )
    parser.add_argument(
        '--projectId',
        help = 'ID (not name) of your project',
        required = True
    )
    parser.add_argument(
        '--outputDir',
        help = 'Top-level directory for TF Records',
        required = True
    )
    
    args = parser.parse_args()
    arguments = args.__dict__

    JOBNAME = 'preprocess-images' + '-' + datetime.datetime.now().strftime('%y%m%d-%H%M%S')
     
    PROJECT = arguments['projectId']
    OUTPUT_DIR = arguments['outputDir']
    if OUTPUT_DIR.startswith('gs://'):
       RUNNER = 'DataflowRunner'
       try:
         subprocess.check_call('gsutil -m rm -r {}'.format(OUTPUT_DIR).split())
       except:
         pass
    else:
       RUNNER = 'DirectRunner'
       shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
       os.makedirs(OUTPUT_DIR)

    # read list of labels
    with tf.gfile.FastGFile(arguments['labelsFile'], 'r') as f:
       LABELS = [line.rstrip() for line in f]
    print('Read in {} labels, from {} to {}'.format(
             len(LABELS), LABELS[0], LABELS[-1]))
    if len(LABELS) < 2:
       print('Require at least two labels')
       sys.exit(-1)
 
    # set up Beam pipeline to convert images to TF Records
    options = {
      'staging_location': os.path.join(OUTPUT_DIR, 'tmp', 'staging'),
      'temp_location': os.path.join(OUTPUT_DIR, 'tmp'),
      'job_name': JOBNAME,
      'project': PROJECT,
      'teardown_policy': 'TEARDOWN_ALWAYS',
      'save_main_session': True
    }
    opts = beam.pipeline.PipelineOptions(flags = [], **options)

    with beam.Pipeline(RUNNER, options=opts) as p:
       # BEAM tasks
       for step in ['train', 'validation']:
          (p 
            | '{}_read_csv'.format(step) >> beam.io.ReadFromText( arguments['{}Csv'.format(step)] )
            | '{}_convert'.format(step)  >> beam.FlatMap(lambda line: convert_to_example(line, LABELS))
            | '{}_write_tfr'.format(step) >> beam.io.tfrecordio.WriteToTFRecord(
                 os.path.join(OUTPUT_DIR, step)) #, file_name_suffix='.gz')
          )


