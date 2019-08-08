# Copyright 2018 Google LLC
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

from __future__ import print_function
import tensorflow as tf
from tensorflow.python.lib.io import file_io as gfile
import numpy as np
import math
import sys

def rnn_multistation_sampling_temperature_sequencer(filenames, resample_by=1, batch_size=sys.maxsize, sequence_size=sys.maxsize, n_forward=0, nb_epochs=1, tminmax=False, keepinmem=True):
    """
    Loads temperature data from CSV files.
    Each data sequence is resampled by "resample_by". Use 1 not to resample.
    The data is also shifted by n_forward after resampling to generate target training sequences.
    n_forward is typically 1 but can be 0 to disable shifting or >1 to train to predict further in advance.
    Each data sequence is split into sequences of size sequence_size. The default is a single sequence with everything.
    Sequences are then assembled in batches of batch_size, sequences from the same weather station
    always on the same line in each batch. batch_size is infinite by default which will result in a batch
    as large as the number of available files.
    When batch_size data files are exhausted, the next batch of files is loaded.
    By default (Tmin, Tmax, interpolated) are returned if tminmax is False. Otherwise (Tmin, Tmax).
    By default, all loaded data is kept in memory and re-served from there. Set keepinmem=False to discard and reload.
    
    Returns epoch, filecount, sample, target, date
      epoch: the epoch number. RNN state should be reset on every epoch change.
      filecount: files loaded in this epoch. RNN state should be reset on every filecount change.
      sample, target: the pair of training samples and targets, of size batch_size or less
      date: sequence of dates corresponding to the samples (assumed the same across batch)
    """
    #filenames = gfile.get_matching_files(filepattern)
    #print('Pattern "{}" matches {} files'.format(filepattern, len(filenames)))
    #filenames = np.array(filenames)
    
    def adjust(ary, n):
        return ary[:ary.shape[0]//n*n]
    
    loaded_samples = {}
    loaded_targets = {}

    for epoch in range(nb_epochs):
        np.random.shuffle(filenames)
        batchlen = len(filenames) % batch_size               # Remainder as
        batchlen = batch_size if batchlen == 0 else batchlen # first smaller batch.
        filebatch = []
        for filecount, filename in enumerate(filenames):
            filebatch.append(filename)
            if len(filebatch) == batchlen:
                if filecount in loaded_samples:
                    # shuffle lines every time the data is reused (this does not appear to be useful though)
                    perm = np.random.permutation(loaded_samples[filecount].shape[1])
                    #print("reshuffling {} rows".format(loaded_samples[filecount].shape[1]))
                    samples = loaded_samples[filecount][:,perm]
                    targets = loaded_targets[filecount][:,perm]
                    #samples = loaded_samples[filecount]
                    #targets = loaded_targets[filecount]
                else:
                    print("Loading {} files".format(batchlen), end="")
                    samples = []
                    targets = []
                    for filename in filebatch:
                        with tf.gfile.Open(filename, mode='rb') as f:
                            # Load min max temperatures from CSV
                            print(".", end="")
                            temperatures = np.genfromtxt(f, delimiter=",", skip_header=True, usecols=[0,1,2,3],
                                                         converters = {0: lambda s: np.datetime64(s)})
                            dates = temperatures[:]['f0']                    # dates
                            temperatures = np.stack([temperatures[:]['f1'],  # min temperatures
                                                     temperatures[:]['f2'],  # max temperatures
                                                     temperatures[:]['f3']], # interpolated
                                                    axis=1) # shape [18262, 3]
                            # Resample temperatures by averaging them across RESAMPLE_BY days
                            temperatures = np.reshape(adjust(temperatures, resample_by), [-1, resample_by, 3]) # [n, RESAMPLE_BY, 3]
                            temperatures = np.mean(temperatures, axis=1) # shape [n, 3]
                            # Shift temperature sequence to generate training targets
                            temp_targets = temperatures[n_forward:]
                            temperatures = temperatures[:temperatures.shape[0]-n_forward] # to allow n_forward=0
                            # Group temperatures into sequences of SEQLEN values
                            nseq = min(sequence_size, temperatures.shape[0]) # If not even full sequence, return everything
                            temp_targets = np.reshape(adjust(temp_targets, nseq), [-1, nseq, 3]) # [p, SEQLEN, 3]
                            temperatures = np.reshape(adjust(temperatures, nseq), [-1, nseq, 3]) # [p, SEQLEN, 3]
                            # do the same with dates, assume all dates identical in all files
                            dates = np.reshape(adjust(dates, resample_by), [-1, resample_by])
                            dates = dates[:dates.shape[0]-n_forward,0] # to allow n_forward=0
                            dates = np.reshape(adjust(dates, nseq), [-1, nseq]) # shape [p, SEQLEN]
                            # Add to batch, temperatures from one file forming a line across batches
                            samples.append(temperatures)
                            targets.append(temp_targets)
                    samples = np.stack(samples, axis=1) # shape [p, BATCHSIZE, SEQLEN, 3]
                    targets = np.stack(targets, axis=1) # shape [p, BATCHSIZE, SEQLEN, 3]
                    # keep them in memory
                    if keepinmem:
                        loaded_samples.update({filecount:samples})
                        loaded_targets.update({filecount:targets})
                    print()
                for sample, target, date in zip(samples, targets, dates):
                    if tminmax:
                        sample = sample[:,:,0:2] # return (Tmin, Tmax) only
                        target = target[:,:,0:2] # return (Tmin, Tmax) only
                    yield sample, target, date, epoch, filecount
                filebatch = []
                batchlen = batch_size

    
def rnn_minibatch_sequencer(data, batch_size, sequence_size, nb_epochs):
    """
    Divides the data into batches of sequences so that all the sequences in one batch
    continue in the next batch. This is a generator that will keep returning batches
    until the input data has been seen nb_epochs times. Sequences are continued even
    between epochs, apart from one, the one corresponding to the end of data.
    The remainder at the end of data that does not fit in an full batch is ignored.
    :param data: the training sequence
    :param batch_size: the size of a training minibatch
    :param sequence_size: the unroll size of the RNN
    :param nb_epochs: number of epochs to train on
    :return:
        x: one batch of training sequences
        y: one batch of target sequences, i.e. training sequences shifted by 1
        epoch: the current epoch number (starting at 0)
    """
    data_len = data.shape[0]
    # using (data_len-1) because we must provide for the sequence shifted by 1 too
    nb_batches = (data_len - 1) // (batch_size * sequence_size)
    assert nb_batches > 0, "Not enough data, even for a single batch. Try using a smaller batch_size."
    rounded_data_len = nb_batches * batch_size * sequence_size
    xdata = np.reshape(data[0:rounded_data_len], [batch_size, nb_batches * sequence_size])
    ydata = np.reshape(data[1:rounded_data_len + 1], [batch_size, nb_batches * sequence_size])

    whole_epochs = math.floor(nb_epochs)
    frac_epoch = nb_epochs - whole_epochs
    last_nb_batch = math.floor(frac_epoch * nb_batches)
    
    for epoch in range(whole_epochs+1):
        for batch in range(nb_batches if epoch < whole_epochs else last_nb_batch):
            x = xdata[:, batch * sequence_size:(batch + 1) * sequence_size]
            y = ydata[:, batch * sequence_size:(batch + 1) * sequence_size]
            x = np.roll(x, -epoch, axis=0)  # to continue the sequence from epoch to epoch (do not reset rnn state!)
            y = np.roll(y, -epoch, axis=0)
            yield x, y, epoch

            
def dumb_minibatch_sequencer(data, batch_size, sequence_size, nb_epochs):
    """
    Divides the data into batches of sequences in the simplest way: sequentially.
    :param data: the training sequence
    :param batch_size: the size of a training minibatch
    :param sequence_size: the unroll size of the RNN
    :param nb_epochs: number of epochs to train on
    :return:
        x: one batch of training sequences
        y: one batch of target sequences, i.e. training sequences shifted by 1
        epoch: the current epoch number (starting at 0)
    """
    data_len = data.shape[0]
    nb_batches = data_len // (batch_size * sequence_size)
    rounded_size = nb_batches * batch_size * sequence_size
    xdata = data[:rounded_size]
    ydata = np.roll(data, -1)[:rounded_size]
    xdata = np.reshape(xdata, [nb_batches, batch_size, sequence_size])
    ydata = np.reshape(ydata, [nb_batches, batch_size, sequence_size])

    for epoch in range(nb_epochs):
        for batch in range(nb_batches):
            yield xdata[batch,:,:], ydata[batch,:,:], epoch
