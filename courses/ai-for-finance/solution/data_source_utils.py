from backtester.instrumentUpdates import *
from backtester.constants import *
from backtester.logger import *
import os
import os.path
import requests
import re
from time import mktime as mktime
from itertools import groupby
import yfinance as yf


def downloadFileFromYahoo(startDate, endDate, instrumentId, fileName, adjustPrice=False):
    logInfo('Downloading %s' % fileName)
    data = yf.download(instrumentId, start=startDate, end=endDate, auto_adjust=adjustPrice)
    data.to_csv(fileName)
    return True

'''
Takes list of instruments.
Outputs them grouped by and sorted by time:
ie [[t1, [i1,i2,i3]],
    [t2, [i4]],
    [t3, [i5, i6]] ], where t1<t2<t3
'''
def groupAndSortByTimeUpdates(instrumentUpdates):
    instrumentUpdates.sort(key=lambda x: x.getTimeOfUpdate())
    groupedInstruments = []
    timeUpdates = []
    # groupby only works on already sorted elements, so we sorted first
    for timeOfUpdate, sameTimeInstruments in groupby(instrumentUpdates, lambda x: x.getTimeOfUpdate()):
        instruments = []
        timeUpdates.append(timeOfUpdate)
        for sameTimeInstrument in sameTimeInstruments:
            instruments.append(sameTimeInstrument)
        groupedInstruments.append([timeOfUpdate, instruments])
    return timeUpdates, groupedInstruments

def getAllTimeStamps(groupedInstrumentUpdates):
    timeUpdates = []
    for timeOfUpdate, instrumentUpdates in groupedInstrumentUpdates:
        timeUpdates.append(timeOfUpdate)
    return timeUpdates
