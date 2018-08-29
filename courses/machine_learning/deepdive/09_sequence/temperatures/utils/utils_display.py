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

import math
import numpy as np
from matplotlib import pyplot as plt
from matplotlib import transforms as plttrans
import utils_prettystyle

def picture_this_1(data, datalen):
    plt.subplot(211)
    plt.plot(data[datalen-512:datalen+512])
    plt.axvspan(0, 512, color='black', alpha=0.06)
    plt.axvspan(512, 1024, color='grey', alpha=0.04)
    plt.subplot(212)
    plt.plot(data[3*datalen-512:3*datalen+512])
    plt.axvspan(0, 512, color='grey', alpha=0.04)
    plt.axvspan(512, 1024, color='black', alpha=0.06)
    plt.show()
    
def picture_this_2(data, batchsize, seqlen):
    samples = np.reshape(data, [-1, batchsize, seqlen])
    rndsample = samples[np.random.choice(samples.shape[0], 8, replace=False)]
    print("Tensor shape of a batch of training sequences: " + str(rndsample[0].shape))
    print("Random excerpt:")
    subplot = 241
    for i in range(8):
        plt.subplot(subplot)
        plt.plot(rndsample[i, 0]) # first sequence in random batch
        subplot += 1
    plt.show()
    
def picture_this_3(Yout_, evaldata, evallabels, seqlen):
    subplot = 241
    colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
    for i in range(8):
        plt.subplot(subplot)
        k = int(np.random.rand() * evaldata.shape[0])
        l0, = plt.plot(evaldata[k, 1:], label="data")
        plt.plot([seqlen-2, seqlen-1], evallabels[k, -2:])
        l1, = plt.plot([seqlen-1], [Yout_[k]], "o", color="red", label='Predicted')
        l2, = plt.plot([seqlen-1], [evallabels[k][-1]], "o", color=colors[1], label='Ground Truth')
        if i==0:
            plt.legend(handles=[l0, l1, l2])
        subplot += 1
    plt.show()
    
def picture_this_4(temperatures, dates):
    min_temps = temperatures[:,0]
    max_temps = temperatures[:,1]
    interpolated = temperatures[:,2]

    interpolated_sequence = False
    #plt.plot(dates, max_temps)
    for i, date in enumerate(dates):
        if interpolated[i]:
            if not interpolated_sequence:
                startdate = date
            interpolated_sequence = True
            stopdate = date
        else:
            if interpolated_sequence:
                # light shade of red just for visibility
                plt.axvspan(startdate+np.timedelta64(-5, 'D'), stopdate+np.timedelta64(6, 'D'), facecolor='#FFCCCC', alpha=1)
                # actual interpolated region
                plt.axvspan(startdate+np.timedelta64(-1, 'D'), stopdate+np.timedelta64(1, 'D'), facecolor='#FF8888', alpha=1)
            interpolated_sequence = False
    plt.fill_between(dates, min_temps, max_temps).set_zorder(10)
    plt.show()
    
def picture_this_5(visu_data, station):
    subplot = 231
    for samples, targets, dates, _, _ in visu_data:
        plt.subplot(subplot)
        h1 = plt.fill_between(dates, samples[station,:,0], samples[station,:,1], label="features")
        h2 = plt.fill_between(dates, targets[station,:,0], targets[station,:,1], label="labels")
        h2.set_zorder(-1)
        if subplot == 231:
            plt.legend(handles=[h1, h2])
        subplot += 1
        if subplot==237:
            break
    plt.show()

def picture_this_6(evaldata, evaldates, prime_data, results, primelen, runlen, offset, rmselen):
    disp_data = evaldata[offset:offset+primelen+runlen]
    disp_dates = evaldates[offset:offset+primelen+runlen]
    colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
    displayresults = np.ma.array(np.concatenate((np.zeros([primelen,2]), results)))
    displayresults = np.ma.masked_where(displayresults == 0, displayresults)
    sp = plt.subplot(212)
    p = plt.fill_between(disp_dates, displayresults[:,0], displayresults[:,1])
    p.set_alpha(0.8)
    p.set_zorder(10)
    trans = plttrans.blended_transform_factory(sp.transData, sp.transAxes)
    plt.text(disp_dates[primelen],0.05,"DATA |", color=colors[1], horizontalalignment="right", transform=trans)
    plt.text(disp_dates[primelen],0.05,"| +PREDICTED", color=colors[0], horizontalalignment="left", transform=trans)
    plt.fill_between(disp_dates, disp_data[:,0], disp_data[:,1])
    plt.axvspan(disp_dates[primelen], disp_dates[primelen+rmselen], color='grey', alpha=0.1, ymin=0.05, ymax=0.95)
    plt.show()

    rmse = math.sqrt(np.mean((evaldata[offset+primelen:offset+primelen+rmselen] - results[:rmselen])**2))
    print("RMSE on {} predictions (shaded area): {}".format(rmselen, rmse))
    
def picture_this_7(features):
    subplot = 231
    for i in range(6):
        plt.subplot(subplot)
        plt.plot(features[i])
        subplot += 1
    plt.show()
    
def picture_this_8(data, prime_data, results, offset, primelen, runlen, rmselen):
    disp_data = data[offset:offset+primelen+runlen]
    colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
    plt.subplot(211)
    plt.text(primelen,2.5,"DATA |", color=colors[1], horizontalalignment="right")
    plt.text(primelen,2.5,"| PREDICTED", color=colors[0], horizontalalignment="left")
    displayresults = np.ma.array(np.concatenate((np.zeros([primelen]), results)))
    displayresults = np.ma.masked_where(displayresults == 0, displayresults)
    plt.plot(displayresults)
    displaydata = np.ma.array(np.concatenate((prime_data, np.zeros([runlen]))))
    displaydata = np.ma.masked_where(displaydata == 0, displaydata)
    plt.plot(displaydata)
    plt.subplot(212)
    plt.text(primelen,2.5,"DATA |", color=colors[1], horizontalalignment="right")
    plt.text(primelen,2.5,"| +PREDICTED", color=colors[0], horizontalalignment="left")
    plt.plot(displayresults)
    plt.plot(disp_data)
    plt.axvspan(primelen, primelen+rmselen, color='grey', alpha=0.1, ymin=0.05, ymax=0.95)
    plt.show()

    rmse = math.sqrt(np.mean((data[offset+primelen:offset+primelen+rmselen] - results[:rmselen])**2))
    print("RMSE on {} predictions (shaded area): {}".format(rmselen, rmse))