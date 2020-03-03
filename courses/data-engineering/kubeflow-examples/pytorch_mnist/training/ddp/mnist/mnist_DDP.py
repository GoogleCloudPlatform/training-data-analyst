#!/usr/bin/env python
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
import datetime
import logging
import os
from math import ceil
from random import Random

import torch
import torch.distributed as dist
import torch.nn as nn  # pylint: disable = all
import torch.nn.functional as F
import torch.optim as optim # pylint: disable = all
import torch.utils.data
import torch.utils.data.distributed
from torch._utils import _flatten_dense_tensors, _unflatten_dense_tensors
from torch.autograd import Variable
from torch.nn.modules import Module
from torchvision import datasets, transforms

gbatch_size = 128


class DistributedDataParallel(Module):
  def __init__(self, module):
    super(DistributedDataParallel, self).__init__()
    self.module = module
    self.first_call = True

    def allreduce_params():
      if self.needs_reduction:
        self.needs_reduction = False  # pylint: disable = attribute-defined-outside-init
        buckets = {}
        for param in self.module.parameters():
          if param.requires_grad and param.grad is not None:
            tp = type(param.data)
            if tp not in buckets:
              buckets[tp] = []
            buckets[tp].append(param)
        for tp in buckets:
          bucket = buckets[tp]
          grads = [param.grad.data for param in bucket]
          coalesced = _flatten_dense_tensors(grads)
          dist.all_reduce(coalesced)
          coalesced /= dist.get_world_size()
          for buf, synced in zip(grads, _unflatten_dense_tensors(coalesced, grads)):
            buf.copy_(synced)

    for param in list(self.module.parameters()):
      def allreduce_hook(*unused):  # pylint: disable = unused-argument
        Variable._execution_engine.queue_callback(allreduce_params)  # pylint: disable = protected-access

      if param.requires_grad:
        param.register_hook(allreduce_hook)

  def weight_broadcast(self):
    for param in self.module.parameters():
      dist.broadcast(param.data, 0)

  def forward(self, *inputs, **kwargs):  # pylint: disable = arguments-differ
    if self.first_call:
      logging.info("first broadcast start")
      self.weight_broadcast()
      self.first_call = False
      logging.info("first broadcast done")
    self.needs_reduction = True  # pylint: disable = attribute-defined-outside-init
    return self.module(*inputs, **kwargs)


class Partition(object):  # pylint: disable = all
  """ Dataset-like object, but only access a subset of it. """

  def __init__(self, data, index):
    self.data = data
    self.index = index

  def __len__(self):
    return len(self.index)

  def __getitem__(self, index):
    data_idx = self.index[index]
    return self.data[data_idx]


class DataPartitioner(object):  # pylint: disable = all
  """ Partitions a dataset into different chuncks. """

  def __init__(self, data, sizes=[0.7, 0.2, 0.1], seed=1234):  # pylint: disable = dangerous-default-value
    self.data = data
    self.partitions = []
    rng = Random()
    rng.seed(seed)
    data_len = len(data)
    indexes = [x for x in range(0, data_len)]
    rng.shuffle(indexes)

    for frac in sizes:
      part_len = int(frac * data_len)
      self.partitions.append(indexes[0:part_len])
      indexes = indexes[part_len:]

  def use(self, partition):
    return Partition(self.data, self.partitions[partition])


class Net(nn.Module):
  """ Network architecture. """

  def __init__(self):
    super(Net, self).__init__()
    self.conv1 = nn.Conv2d(1, 10, kernel_size=5)
    self.conv2 = nn.Conv2d(10, 20, kernel_size=5)
    self.conv2_drop = nn.Dropout2d()
    self.fc1 = nn.Linear(320, 50)
    self.fc2 = nn.Linear(50, 10)

  def forward(self, x):  # pylint: disable = arguments-differ
    x = F.relu(F.max_pool2d(self.conv1(x), 2))
    x = F.relu(F.max_pool2d(self.conv2_drop(self.conv2(x)), 2))
    x = x.view(-1, 320)
    x = F.relu(self.fc1(x))
    x = F.dropout(x, training=self.training)
    x = self.fc2(x)
    return F.log_softmax(x)


def partition_dataset(rank):
  """ Partitioning MNIST """
  dataset = datasets.MNIST(
    './data{}'.format(rank),
    train=True,
    download=True,
    transform=transforms.Compose([
      transforms.ToTensor(),
      transforms.Normalize((0.1307,), (0.3081,))
    ]))
  size = dist.get_world_size()
  bsz = int(gbatch_size / float(size))
  train_sampler = torch.utils.data.distributed.DistributedSampler(dataset)
  train_set = torch.utils.data.DataLoader(
    dataset, batch_size=bsz, shuffle=(train_sampler is None), sampler=train_sampler)
  return train_set, bsz


def average_gradients(model):
  """ Gradient averaging. """
  size = float(dist.get_world_size())
  group = dist.new_group([0])
  for param in model.parameters():
    dist.all_reduce(param.grad.data, op=dist.reduce_op.SUM, group=group)
    param.grad.data /= size


def run(modelpath, gpu):
  """ Distributed Synchronous SGD Example """
  rank = dist.get_rank()
  torch.manual_seed(1234)
  train_set, bsz = partition_dataset(rank)
  model = Net()
  if gpu:
    model = model.cuda()
    model = torch.nn.parallel.DistributedDataParallel(model)
  else:
    model = DistributedDataParallel(model)
  optimizer = optim.SGD(model.parameters(), lr=0.01, momentum=0.5)
  model_dir = modelpath

  num_batches = ceil(len(train_set.dataset) / float(bsz))
  logging.info("num_batches = %s", num_batches)
  time_start = datetime.datetime.now()
  for epoch in range(3):
    epoch_loss = 0.0
    for data, target in train_set:
      if gpu:
        data, target = Variable(data).cuda(), Variable(target).cuda()
      else:
        data, target = Variable(data), Variable(target)
      optimizer.zero_grad()
      output = model(data)
      loss = F.nll_loss(output, target)
      epoch_loss += loss.item()
      loss.backward()
      average_gradients(model)
      optimizer.step()
    logging.info('Epoch {} Loss {:.6f} Global batch size {} on {} ranks'.format(
      epoch, epoch_loss / num_batches, gbatch_size, dist.get_world_size()))
  # Ensure only the master node saves the model
  main_proc = rank == 0
  if main_proc:
    if not os.path.exists(model_dir):
      os.makedirs(model_dir)
    if gpu:
      model_path = model_dir + "/model_gpu.dat"
    else:
      model_path = model_dir + "/model_cpu.dat"
    logging.info("Saving model in {}".format(model_path))  # pylint: disable = logging-format-interpolation
    torch.save(model.module.state_dict(), model_path)
  if gpu:
    logging.info("GPU training time= {}".format(  # pylint: disable = logging-format-interpolation
      str(datetime.datetime.now() - time_start)))  # pylint: disable = logging-format-interpolation
  else:
    logging.info("CPU training time= {}".format(  # pylint: disable = logging-format-interpolation
      str(datetime.datetime.now() - time_start)))  # pylint: disable = logging-format-interpolation


if __name__ == "__main__":
  import argparse
  logging.basicConfig(level=logging.INFO,
                      format=('%(levelname)s|%(asctime)s'
                              '|%(pathname)s|%(lineno)d| %(message)s'),
                      datefmt='%Y-%m-%dT%H:%M:%S',
                      )
  logging.getLogger().setLevel(logging.INFO)

  parser = argparse.ArgumentParser(description='Train Pytorch MNIST model using DDP')
  parser.add_argument('--gpu', action='store_true',
                      help='Use GPU and CUDA')
  parser.set_defaults(gpu=False)
  parser.add_argument('--modelpath', metavar='path', required=True,
                      help='Path to model, e.g., /mnt/kubeflow-gcfs/pytorch/model')
  args = parser.parse_args()
  if args.gpu:
    logging.info("\n======= CUDA INFO =======")
    logging.info("CUDA Availibility: %s", torch.cuda.is_available())
    if torch.cuda.is_available():
      logging.info("CUDA Device Name: %s", torch.cuda.get_device_name(0))
      logging.info("CUDA Version: %s", torch.version.cuda)
    logging.info("=========================\n")
  dist.init_process_group(backend='gloo')
  run(modelpath=args.modelpath, gpu=args.gpu)
  dist.destroy_process_group()
