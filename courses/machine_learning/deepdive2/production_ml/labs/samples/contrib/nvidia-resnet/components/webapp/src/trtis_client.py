#!/usr/bin/env python2.7
'''
Copyright 2018 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

from __future__ import print_function

import numpy as np
import os
import random
from builtins import range
from functools import partial
import grpc

from tensorrtserver.api import api_pb2
from tensorrtserver.api import grpc_service_pb2
from tensorrtserver.api import grpc_service_pb2_grpc
import tensorrtserver.api.model_config_pb2 as model_config

from PIL import Image


def model_dtype_to_np(model_dtype):
  if model_dtype == model_config.TYPE_BOOL:
    return np.bool
  elif model_dtype == model_config.TYPE_INT8:
    return np.int8
  elif model_dtype == model_config.TYPE_INT16:
    return np.int16
  elif model_dtype == model_config.TYPE_INT32:
    return np.int32
  elif model_dtype == model_config.TYPE_INT64:
    return np.int64
  elif model_dtype == model_config.TYPE_UINT8:
    return np.uint8
  elif model_dtype == model_config.TYPE_UINT16:
    return np.uint16
  elif model_dtype == model_config.TYPE_FP16:
    return np.float16
  elif model_dtype == model_config.TYPE_FP32:
    return np.float32
  elif model_dtype == model_config.TYPE_FP64:
    return np.float64
  elif model_dtype == model_config.TYPE_STRING:
    return np.dtype(object)
  return None


def parse_model(status, model_name, batch_size, verbose=False):
  """
  Check the configuration of a model to make sure it meets the
  requirements for an image classification network (as expected by
  this client)
  """
  server_status = status.server_status
  if model_name not in server_status.model_status.keys():
    raise Exception("unable to get status for '" + model_name + "'")

  status = server_status.model_status[model_name]
  config = status.config

  if len(config.input) != 1:
    raise Exception("expecting 1 input, got {}".format(len(config.input)))
  if len(config.output) != 1:
    raise Exception("expecting 1 output, got {}".format(len(config.output)))

  input = config.input[0]
  output = config.output[0]

  if output.data_type != model_config.TYPE_FP32:
    raise Exception("expecting output datatype to be TYPE_FP32, model '" +
                    model_name + "' output type is " +
                    model_config.DataType.Name(output.data_type))

  # Output is expected to be a vector. But allow any number of
  # dimensions as long as all but 1 is size 1 (e.g. { 10 }, { 1, 10
  # }, { 10, 1, 1 } are all ok).
  non_one_cnt = 0
  for dim in output.dims:
    if dim > 1:
      non_one_cnt += 1
      if non_one_cnt > 1:
        raise Exception("expecting model output to be a vector")

  # Model specifying maximum batch size of 0 indicates that batching
  # is not supported and so the input tensors do not expect an "N"
  # dimension (and 'batch_size' should be 1 so that only a single
  # image instance is inferred at a time).
  max_batch_size = config.max_batch_size
  if max_batch_size == 0:
    if batch_size != 1:
      raise Exception("batching not supported for model '" + model_name + "'")
  else:  # max_batch_size > 0
    if batch_size > max_batch_size:
      raise Exception(
        "expecting batch size <= {} for model '{}'".format(max_batch_size, model_name))

  # Model input must have 3 dims, either CHW or HWC
  if len(input.dims) != 3:
    raise Exception(
      "expecting input to have 3 dimensions, model '{}' input has {}".format(
        model_name, len(input.dims)))

  if ((input.format != model_config.ModelInput.FORMAT_NCHW) and
      (input.format != model_config.ModelInput.FORMAT_NHWC)):
    raise Exception("unexpected input format " + model_config.ModelInput.Format.Name(input.format) +
                    ", expecting " +
                    model_config.ModelInput.Format.Name(model_config.ModelInput.FORMAT_NCHW) +
                    " or " +
                    model_config.ModelInput.Format.Name(model_config.ModelInput.FORMAT_NHWC))

  if input.format == model_config.ModelInput.FORMAT_NHWC:
    h = input.dims[0]
    w = input.dims[1]
    c = input.dims[2]
  else:
    c = input.dims[0]
    h = input.dims[1]
    w = input.dims[2]

  return (input.name, output.name, c, h, w, input.format, model_dtype_to_np(input.data_type))


def preprocess(img, format, dtype, c, h, w):
  """
  Pre-process an image to meet the size, type and format
  requirements specified by the parameters.
  """
  # np.set_printoptions(threshold='nan')

  if c == 1:
    sample_img = img.convert('L')
  else:
    sample_img = img.convert('RGB')

  resized_img = sample_img.resize((w, h), Image.BILINEAR)
  resized = np.array(resized_img)
  if resized.ndim == 2:
    resized = resized[:, :, np.newaxis]

  typed = resized.astype(dtype)

  scaled = (typed / 255) - 0.5

  # Channels are in RGB order. Currently model configuration data
  # doesn't provide any information as to other channel orderings
  # (like BGR) so we just assume RGB.
  return scaled


def postprocess(results, filenames, batch_size):
  """
  Post-process results to show classifications.
  """
  if len(results) != 1:
    raise Exception("expected 1 result, got {}".format(len(results)))

  batched_result = results[0].batch_classes
  if len(batched_result) != batch_size:
    raise Exception("expected {} results, got {}".format(batch_size, len(batched_result)))
  if len(filenames) != batch_size:
    raise Exception("expected {} filenames, got {}".format(batch_size, len(filenames)))

  label, score = [], []
  # batch size is always 1 here, need to modify if were to larger batch_size
  for (index, result) in enumerate(batched_result):
    print("Image '{}':".format(filenames[index]))
    for cls in result.cls:
      label.append(cls.label)
      score += [{"index": cls.label, "val": cls.value}]
      print("    {} ({}) = {}".format(cls.idx, cls.label, cls.value))
  return label[0], score


def requestGenerator(input_name, output_name, c, h, w, format, dtype, model_name, model_version, image_filename,
                     result_filenames):
  # Prepare request for Infer gRPC
  # The meta data part can be reused across requests
  request = grpc_service_pb2.InferRequest()
  request.model_name = model_name
  if model_version is None:
    request.model_version = -1
  else:
    request.model_version = model_version
  # optional pass in a batch size for generate requester over a set of image files, need to refactor
  batch_size = 1
  request.meta_data.batch_size = batch_size
  output_message = api_pb2.InferRequestHeader.Output()
  output_message.name = output_name
  # Number of class results to report. Default is 10 to match with demo.
  output_message.cls.count = 10
  request.meta_data.output.extend([output_message])

  filenames = []
  if os.path.isdir(image_filename):
    filenames = [os.path.join(image_filename, f)
                 for f in os.listdir(image_filename)
                 if os.path.isfile(os.path.join(image_filename, f))]
  else:
    filenames = [image_filename, ]

  filenames.sort()

  # Preprocess the images into input data according to model
  # requirements
  image_data = []
  for filename in filenames:
    img = Image.open(filename)
    image_data.append(preprocess(img, format, dtype, c, h, w))

  request.meta_data.input.add(name=input_name)

  # Send requests of batch_size images. If the number of
  # images isn't an exact multiple of batch_size then just
  # start over with the first images until the batch is filled.
  image_idx = 0
  last_request = False
  while not last_request:
    input_bytes = None
    input_filenames = []
    del request.raw_input[:]
    for idx in range(batch_size):
      input_filenames.append(filenames[image_idx])
      if input_bytes is None:
        input_bytes = image_data[image_idx].tobytes()
      else:
        input_bytes += image_data[image_idx].tobytes()

      image_idx = (image_idx + 1) % len(image_data)
      if image_idx == 0:
        last_request = True

    request.raw_input.extend([input_bytes])
    result_filenames.append(input_filenames)
    yield request


def get_prediction(image_filename, server_host='localhost', server_port=8001,
                   model_name="end2end-demo", model_version=None):
  """
  Retrieve a prediction from a TensorFlow model server

  :param image:       a end2end-demo image
  :param server_host: the address of the TensorRT inference server
  :param server_port: the port used by the server
  :param model_name: the name of the model
  :param timeout:     the amount of time to wait for a prediction to complete
  :return 0:          the integer predicted in the end2end-demo image
  :return 1:          the confidence scores for all classes
  """
  channel = grpc.insecure_channel(server_host + ':' + str(server_port))
  grpc_stub = grpc_service_pb2_grpc.GRPCServiceStub(channel)

  # Prepare request for Status gRPC
  request = grpc_service_pb2.StatusRequest(model_name=model_name)
  # Call and receive response from Status gRPC
  response = grpc_stub.Status(request)
  # Make sure the model matches our requirements, and get some
  # properties of the model that we need for preprocessing
  batch_size = 1
  verbose = False
  input_name, output_name, c, h, w, format, dtype = parse_model(
    response, model_name, batch_size, verbose)

  filledRequestGenerator = partial(requestGenerator, input_name, output_name, c, h, w, format, dtype, model_name,
                                   model_version, image_filename)

  # Send requests of batch_size images. If the number of
  # images isn't an exact multiple of batch_size then just
  # start over with the first images until the batch is filled.
  result_filenames = []
  requests = []
  responses = []

  # Send request
  for request in filledRequestGenerator(result_filenames):
    responses.append(grpc_stub.Infer(request))

  # For async, retrieve results according to the send order
  for request in requests:
    responses.append(request.result())

  idx = 0
  for response in responses:
    print("Request {}, batch size {}".format(idx, batch_size))
    label, score = postprocess(response.meta_data.output, result_filenames[idx], batch_size)
    idx += 1

  return label, score


def random_image(img_path='/workspace/web_server/static/images'):
  """
  Pull a random image out of the small end2end-demo dataset

  :param savePath: the path to save the file to. If None, file is not saved
  :return 0: file selected
  :return 1: label selelcted
  """
  random_dir = random.choice(os.listdir(img_path))
  random_file = random.choice(os.listdir(img_path + '/' + random_dir))

  return img_path + '/' + random_dir + '/' + random_file, random_dir, 'static/images' + '/' + random_dir + '/' + random_file
