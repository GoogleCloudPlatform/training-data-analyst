import os, sys
from datetime import datetime
from backtester.instrumentUpdates import *
from backtester.constants import *
from backtester.logger import *
from backtester.dataSource.data_source import DataSource
import csv
import pandas as pd
import os
import os.path
from backtester.dataSource.data_source_utils import downloadFileFromYahoo
import backtester.dataSource.data_source_utils as data_source_utils




TYPE_LINE_UNDEFINED = 0
TYPE_LINE_HEADER = 1
TYPE_LINE_DATA = 2


def checkDate(lineItem):
    try:
        datetime.strptime(lineItem, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def checkTimestamp(lineItem):
    return True


def isFloat(string):
    try:
        return float(string) or float(string) == 0.0
    except ValueError:  # if string is not a number
        return False

# Returns the type of lineItems


def validateLineItem(lineItems):
    if len(lineItems) == 7:
        if lineItems[0] == "Date":
            return TYPE_LINE_HEADER
        elif checkDate(lineItems[0]) and isFloat(lineItems[1]) and isFloat(lineItems[2]) and isFloat(lineItems[3]) and isFloat(lineItems[4]) and isFloat(lineItems[5]):
            return TYPE_LINE_DATA
    return TYPE_LINE_UNDEFINED


def parseDataLine(lineItems):
    if (len(lineItems) != 7):
        return None
    openPrice = float(lineItems[1])
    high = float(lineItems[2])
    low = float(lineItems[3])
    closePrice = float(lineItems[4])
    adjustedClose = float(lineItems[5])
    volume = float(lineItems[6])
    return {'open': openPrice,
            'high': high,
            'low': low,
            'close': closePrice,
            'adjClose' : adjustedClose,
            'volume': volume}

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

class InstrumentsFromFile():
    def __init__(self, fileName, instrumentId):
        self.fileName = fileName
        self.instrumentId = instrumentId
        self.currentInstrumentSymbol = instrumentId
        self.currentTimeOfUpdate = None
        self.currentBookData = None

    def processLine(self, line):
        lineItems = line.split(',')
        lineItemType = validateLineItem(lineItems)
        if (lineItemType == TYPE_LINE_DATA):
            inst = None
            if self.currentInstrumentSymbol is not None:
                self.currentTimeOfUpdate = datetime.strptime(lineItems[0], "%Y-%m-%d")
                self.currentInstrumentSymbol = self.instrumentId
                self.currentBookData = parseDataLine(lineItems)
                if self.currentBookData is None:
                    return None
                # right now only works for stocks
                inst = StockInstrumentUpdate(stockInstrumentId=self.instrumentId,
                                             tradeSymbol=self.currentInstrumentSymbol,
                                             timeOfUpdate=self.currentTimeOfUpdate,
                                             bookData=self.currentBookData)
                return inst
        return None

    def processLinesIntoInstruments(self):
        with open(self.fileName, "r") as ins:
            instruments = []
            for line in ins:
                inst = self.processLine(line)
                if inst is not None:
                    instruments.append(inst)
            return instruments


class YahooStockDataSource(DataSource):
    def __init__(self, cachedFolderName, dataSetId, instrumentIds, startDateStr, endDateStr, event='history', adjustPrice=False, downloadId=".NS", liveUpdates=True, pad=True):
        super(YahooStockDataSource, self).__init__(cachedFolderName, dataSetId, instrumentIds, startDateStr, endDateStr)
        self.__dateAppend = "_%sto%s"%(datetime.strptime(startDateStr, '%Y/%m/%d').strftime('%Y-%m-%d'),datetime.strptime(startDateStr, '%Y/%m/%d').strftime('%Y-%m-%d'))
        self.__downloadId = downloadId
        self.__bookDataByFeature = {}
        self.__adjustPrice = adjustPrice
        self.currentDate = self._startDate
        self.event = event
        if liveUpdates:
            self._allTimes, self._groupedInstrumentUpdates = self.getGroupedInstrumentUpdates()
            self.processGroupedInstrumentUpdates()
            self._bookDataFeatureKeys = self.__bookDataByFeature.keys()
        else:
            self._allTimes, self._bookDataByInstrument = self.getAllInstrumentUpdates()
            if pad:
                self.padInstrumentUpdates()
            self.filterUpdatesByDates([(startDateStr, endDateStr)])

    def getFileName(self, instrumentId):
        return self._cachedFolderName + self._dataSetId + '/' + instrumentId + '%s.csv'%self.__dateAppend

    def downloadAndAdjustData(self, instrumentId, fileName):
        if not os.path.isfile(fileName):
            if not downloadFileFromYahoo(self._startDate, self._endDate, instrumentId, fileName, adjustPrice=self.__adjustPrice):
                logError('Skipping %s:' % (instrumentId))
                return False
        return True

    def processGroupedInstrumentUpdates(self):
        timeUpdates = self._allTimes
        limits = [0.20, 0.40, 0.60, 0.80, 1.0]
        if (len(self._instrumentIds) > 30):
            limits = [0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.0]
        currentLimitIdx = 0
        idx = 0.0
        for timeOfUpdate, instrumentUpdates in self._groupedInstrumentUpdates:
            idx = idx + 1.0
            if (idx / len(timeUpdates)) > limits[currentLimitIdx]:
                print ('%d%% done...' % (limits[currentLimitIdx] * 100))
                currentLimitIdx = currentLimitIdx + 1
            for instrumentUpdate in instrumentUpdates:
                bookData = instrumentUpdate.getBookData()
                for featureKey in bookData:
                    # TODO: Fix for python 3
                    if featureKey not in self.__bookDataByFeature:
                        self.__bookDataByFeature[featureKey] = pd.DataFrame(columns=self._instrumentIds,
                                                                            index=timeUpdates)
                    self.__bookDataByFeature[featureKey].at[timeOfUpdate, instrumentUpdate.getInstrumentId()] = bookData[featureKey]
        for featureKey in self.__bookDataByFeature:
            self.__bookDataByFeature[featureKey].fillna(method='pad', inplace=True)

    def getInstrumentUpdateFromRow(self, instrumentId, row):
        bookData =  {'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'adjClose' : float(row['Adj Close']),
                    'volume': float(row['Volume'])}

        timeOfUpdate = datetime.strptime(row['Date'], '%Y-%m-%d')
        inst = StockInstrumentUpdate(stockInstrumentId=instrumentId,
                                     tradeSymbol=instrumentId,
                                     timeOfUpdate=timeOfUpdate,
                                     bookData=bookData)
        return inst

    def getBookDataByFeature(self):
        return self.__bookDataByFeature

    def getClosingTime(self):
        return self._allTimes[-1]


if __name__ == "__main__":
    instrumentIds = ['IBM', 'AAPL']
    startDateStr = '2013/05/10'
    endDateStr = '2017/06/09'
    yds = YahooStockDataSource(cachedFolderName='yahooData/',
                                     dataSetId="testTrading",
                                     instrumentIds=instrumentIds,
                                     startDateStr=startDateStr,
                                     endDateStr=endDateStr,
                                     event='history',
                                     liveUpdates=False)
    print(next(yds.emitAllInstrumentUpdates()['IBM'].getBookDataChunk(100)))
    print(yds.getBookDataFeatures())
