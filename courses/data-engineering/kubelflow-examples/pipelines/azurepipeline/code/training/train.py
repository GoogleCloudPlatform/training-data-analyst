from __future__ import absolute_import, division, print_function
import os
import math
import hmac
import json
import hashlib
import argparse
from random import shuffle
from pathlib2 import Path
import numpy as np
import tensorflow as tf
from tensorflow.data import Dataset


def info(msg, char="#", width=75):
  print("")
  print(char * width)
  print(char + "   %0*s" % ((-1 * width) + 5, msg) + char)
  print(char * width)


def check_dir(path):
  if not os.path.exists(path):
    os.makedirs(path)
  return Path(path).resolve(strict=False)


def process_image(path, label, img_size):
  img_raw = tf.io.read_file(path)
  img_tensor = tf.image.decode_jpeg(img_raw, channels=3)
  img_final = tf.image.resize(img_tensor, [img_size, img_size]) / 255
  return img_final, label


def load_dataset(base_path, dset, split=None):
  # normalize splits
  if split is None:
    split = [8, 1, 1]
  splits = np.array(split) / np.sum(np.array(split))

  # find labels - parent folder names
  labels = {}
  for (_, dirs, _) in os.walk(base_path):
    print('found {}'.format(dirs))
    labels = {k: v for (v, k) in enumerate(dirs)}
    print('using {}'.format(labels))
    break

  # load all files along with idx label
  print('loading dataset from {}'.format(dset))
  with open(dset, 'r') as d:
    data = [(str(Path(line.strip()).absolute()),
             labels[Path(line.strip()).parent.name]) for line in d.readlines()]

  print('dataset size: {}\nsuffling data...'.format(len(data)))

  # shuffle data
  shuffle(data)

  print('splitting data...')
  # split data
  train_idx = int(len(data) * splits[0])

  return data[:train_idx]


# @print_info
def run(
    dpath,
    img_size=160,
    epochs=10,
    batch_size=32,
    learning_rate=0.0001,
    output='model',
    dset=None):
  img_shape = (img_size, img_size, 3)

  info('Loading Data Set')
  # load dataset
  train = load_dataset(dpath, dset)

  # training data
  train_data, train_labels = zip(*train)
  train_ds = Dataset.zip((Dataset.from_tensor_slices(list(train_data)),
                          Dataset.from_tensor_slices(list(train_labels)), img_size))

  train_ds = train_ds.map(map_func=process_image,
                          num_parallel_calls=5)

  train_ds = train_ds.apply(tf.data.experimental.ignore_errors())

  train_ds = train_ds.batch(batch_size)
  train_ds = train_ds.prefetch(buffer_size=5)
  train_ds = train_ds.repeat()

  # model
  info('Creating Model')
  base_model = tf.keras.applications.MobileNetV2(input_shape=img_shape,
                                                 include_top=False,
                                                 weights='imagenet')
  base_model.trainable = True

  model = tf.keras.Sequential([
    base_model,
    tf.keras.layers.GlobalAveragePooling2D(),
    tf.keras.layers.Dense(1, activation='sigmoid')
  ])

  model.compile(optimizer=tf.keras.optimizers.Adam(lr=learning_rate),
                loss='binary_crossentropy',
                metrics=['accuracy'])

  model.summary()

  # training
  info('Training')
  steps_per_epoch = math.ceil(len(train) / batch_size)
  model.fit(train_ds, epochs=epochs, steps_per_epoch=steps_per_epoch)

  # save model
  info('Saving Model')

  # check existence of base model folder
  output = check_dir(output)

  print('Serializing into saved_model format')
  tf.saved_model.save(model, str(output))
  print('Done!')

  # add time prefix folder
  file_output = str(Path(output).joinpath('latest.h5'))
  print('Serializing h5 model to:\n{}'.format(file_output))
  model.save(file_output)

  return generate_hash(file_output, 'kf_pipeline')


def generate_hash(dfile, key):
  print('Generating hash for {}'.format(dfile))
  m = hmac.new(str.encode(key), digestmod=hashlib.sha256)
  BUF_SIZE = 65536
  with open(str(dfile), 'rb') as myfile:
    while True:
      data = myfile.read(BUF_SIZE)
      if not data:
        break
      m.update(data)

  return m.hexdigest()


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='transfer learning for binary image task')
  parser.add_argument('-s', '--base_path', help='directory to base data', default='../../data')
  parser.add_argument('-d', '--data', help='directory to training and test data', default='train')
  parser.add_argument('-e', '--epochs', help='number of epochs', default=10, type=int)
  parser.add_argument('-b', '--batch', help='batch size', default=32, type=int)
  parser.add_argument('-i', '--image_size', help='image size', default=160, type=int)
  parser.add_argument('-l', '--lr', help='learning rate', default=0.0001, type=float)
  parser.add_argument('-o', '--outputs', help='output directory', default='model')
  parser.add_argument('-f', '--dataset', help='cleaned data listing')
  args = parser.parse_args()

  info('Using TensorFlow v.{}'.format(tf.__version__))

  data_path = Path(args.base_path).joinpath(args.data).resolve(strict=False)
  target_path = Path(args.base_path).resolve(strict=False).joinpath(args.outputs)
  dataset = Path(args.base_path).joinpath(args.dataset)
  image_size = args.image_size

  params = Path(args.base_path).joinpath('params.json')

  args = {
    "dpath": str(data_path),
    "img_size": image_size,
    "epochs": args.epochs,
    "batch_size": args.batch,
    "learning_rate": args.lr,
    "output": str(target_path),
    "dset": str(dataset)
  }

  dataset_signature = generate_hash(dataset, 'kf_pipeline')
  # printing out args for posterity
  for i in args:
    print('{} => {}'.format(i, args[i]))

  model_signature = run(**args)

  args['dataset_signature'] = dataset_signature.upper()
  args['model_signature'] = model_signature.upper()
  args['model_type'] = 'tfv2-MobileNetV2'
  print('Writing out params...', end='')
  with open(str(params), 'w') as f:
    json.dump(args, f)

  print(' Saved to {}'.format(str(params)))

  # python train.py -d train -e 3 -b 32 -l 0.0001 -o model -f train.txt
