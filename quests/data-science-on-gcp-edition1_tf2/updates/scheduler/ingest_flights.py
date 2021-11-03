#!/usr/bin/env python

# Copyright 2016 Google Inc.
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

import os
import shutil
import logging
import os.path
import zipfile
import datetime
import tempfile
from google.cloud import storage
from google.cloud.storage import Blob

try:
    from urllib.request import urlopen as impl
    import ssl

    ctx_no_secure = ssl.create_default_context()
    ctx_no_secure.set_ciphers('HIGH:!DH:!aNULL')
    ctx_no_secure.check_hostname = False
    ctx_no_secure.verify_mode = ssl.CERT_NONE
    # For Python 3.0 and later
    def urlopen(url, data):
        return impl(url, data.encode('utf-8'), context=ctx_no_secure)
    def remove_quote(text):
        return text.translate(str.maketrans('','', '"'))
except ImportError as error:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen
    def remove_quote(text):
        return text.translate(None, '"')

def download(YEAR, MONTH, destdir):
   '''
     Downloads on-time performance data and returns local filename
     YEAR e.g.'2015'
     MONTH e.g. '01 for January
   '''
   logging.info('Requesting data for {}-{}-*'.format(YEAR, MONTH))

   PARAMS="UserTableName=On_Time_Performance&DBShortName=&RawDataTable=T_ONTIME&sqlstr=+SELECT+FL_DATE%2CUNIQUE_CARRIER%2CAIRLINE_ID%2CCARRIER%2CFL_NUM%2CORIGIN_AIRPORT_ID%2CORIGIN_AIRPORT_SEQ_ID%2CORIGIN_CITY_MARKET_ID%2CORIGIN%2CDEST_AIRPORT_ID%2CDEST_AIRPORT_SEQ_ID%2CDEST_CITY_MARKET_ID%2CDEST%2CCRS_DEP_TIME%2CDEP_TIME%2CDEP_DELAY%2CTAXI_OUT%2CWHEELS_OFF%2CWHEELS_ON%2CTAXI_IN%2CCRS_ARR_TIME%2CARR_TIME%2CARR_DELAY%2CCANCELLED%2CCANCELLATION_CODE%2CDIVERTED%2CDISTANCE+FROM++T_ONTIME+WHERE+Month+%3D{1}+AND+YEAR%3D{0}&varlist=FL_DATE%2CUNIQUE_CARRIER%2CAIRLINE_ID%2CCARRIER%2CFL_NUM%2CORIGIN_AIRPORT_ID%2CORIGIN_AIRPORT_SEQ_ID%2CORIGIN_CITY_MARKET_ID%2CORIGIN%2CDEST_AIRPORT_ID%2CDEST_AIRPORT_SEQ_ID%2CDEST_CITY_MARKET_ID%2CDEST%2CCRS_DEP_TIME%2CDEP_TIME%2CDEP_DELAY%2CTAXI_OUT%2CWHEELS_OFF%2CWHEELS_ON%2CTAXI_IN%2CCRS_ARR_TIME%2CARR_TIME%2CARR_DELAY%2CCANCELLED%2CCANCELLATION_CODE%2CDIVERTED%2CDISTANCE&grouplist=&suml=&sumRegion=&filter1=title%3D&filter2=title%3D&geo=All%A0&time=March&timename=Month&GEOGRAPHY=All&XYEAR={0}&FREQUENCY=3&VarDesc=Year&VarType=Num&VarDesc=Quarter&VarType=Num&VarDesc=Month&VarType=Num&VarDesc=DayofMonth&VarType=Num&VarDesc=DayOfWeek&VarType=Num&VarName=FL_DATE&VarDesc=FlightDate&VarType=Char&VarName=UNIQUE_CARRIER&VarDesc=UniqueCarrier&VarType=Char&VarName=AIRLINE_ID&VarDesc=AirlineID&VarType=Num&VarName=CARRIER&VarDesc=Carrier&VarType=Char&VarDesc=TailNum&VarType=Char&VarName=FL_NUM&VarDesc=FlightNum&VarType=Char&VarName=ORIGIN_AIRPORT_ID&VarDesc=OriginAirportID&VarType=Num&VarName=ORIGIN_AIRPORT_SEQ_ID&VarDesc=OriginAirportSeqID&VarType=Num&VarName=ORIGIN_CITY_MARKET_ID&VarDesc=OriginCityMarketID&VarType=Num&VarName=ORIGIN&VarDesc=Origin&VarType=Char&VarDesc=OriginCityName&VarType=Char&VarDesc=OriginState&VarType=Char&VarDesc=OriginStateFips&VarType=Char&VarDesc=OriginStateName&VarType=Char&VarDesc=OriginWac&VarType=Num&VarName=DEST_AIRPORT_ID&VarDesc=DestAirportID&VarType=Num&VarName=DEST_AIRPORT_SEQ_ID&VarDesc=DestAirportSeqID&VarType=Num&VarName=DEST_CITY_MARKET_ID&VarDesc=DestCityMarketID&VarType=Num&VarName=DEST&VarDesc=Dest&VarType=Char&VarDesc=DestCityName&VarType=Char&VarDesc=DestState&VarType=Char&VarDesc=DestStateFips&VarType=Char&VarDesc=DestStateName&VarType=Char&VarDesc=DestWac&VarType=Num&VarName=CRS_DEP_TIME&VarDesc=CRSDepTime&VarType=Char&VarName=DEP_TIME&VarDesc=DepTime&VarType=Char&VarName=DEP_DELAY&VarDesc=DepDelay&VarType=Num&VarDesc=DepDelayMinutes&VarType=Num&VarDesc=DepDel15&VarType=Num&VarDesc=DepartureDelayGroups&VarType=Num&VarDesc=DepTimeBlk&VarType=Char&VarName=TAXI_OUT&VarDesc=TaxiOut&VarType=Num&VarName=WHEELS_OFF&VarDesc=WheelsOff&VarType=Char&VarName=WHEELS_ON&VarDesc=WheelsOn&VarType=Char&VarName=TAXI_IN&VarDesc=TaxiIn&VarType=Num&VarName=CRS_ARR_TIME&VarDesc=CRSArrTime&VarType=Char&VarName=ARR_TIME&VarDesc=ArrTime&VarType=Char&VarName=ARR_DELAY&VarDesc=ArrDelay&VarType=Num&VarDesc=ArrDelayMinutes&VarType=Num&VarDesc=ArrDel15&VarType=Num&VarDesc=ArrivalDelayGroups&VarType=Num&VarDesc=ArrTimeBlk&VarType=Char&VarName=CANCELLED&VarDesc=Cancelled&VarType=Num&VarName=CANCELLATION_CODE&VarDesc=CancellationCode&VarType=Char&VarName=DIVERTED&VarDesc=Diverted&VarType=Num&VarDesc=CRSElapsedTime&VarType=Num&VarDesc=ActualElapsedTime&VarType=Num&VarDesc=AirTime&VarType=Num&VarDesc=Flights&VarType=Num&VarName=DISTANCE&VarDesc=Distance&VarType=Num&VarDesc=DistanceGroup&VarType=Num&VarDesc=CarrierDelay&VarType=Num&VarDesc=WeatherDelay&VarType=Num&VarDesc=NASDelay&VarType=Num&VarDesc=SecurityDelay&VarType=Num&VarDesc=LateAircraftDelay&VarType=Num&VarDesc=FirstDepTime&VarType=Char&VarDesc=TotalAddGTime&VarType=Num&VarDesc=LongestAddGTime&VarType=Num&VarDesc=DivAirportLandings&VarType=Num&VarDesc=DivReachedDest&VarType=Num&VarDesc=DivActualElapsedTime&VarType=Num&VarDesc=DivArrDelay&VarType=Num&VarDesc=DivDistance&VarType=Num&VarDesc=Div1Airport&VarType=Char&VarDesc=Div1AirportID&VarType=Num&VarDesc=Div1AirportSeqID&VarType=Num&VarDesc=Div1WheelsOn&VarType=Char&VarDesc=Div1TotalGTime&VarType=Num&VarDesc=Div1LongestGTime&VarType=Num&VarDesc=Div1WheelsOff&VarType=Char&VarDesc=Div1TailNum&VarType=Char&VarDesc=Div2Airport&VarType=Char&VarDesc=Div2AirportID&VarType=Num&VarDesc=Div2AirportSeqID&VarType=Num&VarDesc=Div2WheelsOn&VarType=Char&VarDesc=Div2TotalGTime&VarType=Num&VarDesc=Div2LongestGTime&VarType=Num&VarDesc=Div2WheelsOff&VarType=Char&VarDesc=Div2TailNum&VarType=Char&VarDesc=Div3Airport&VarType=Char&VarDesc=Div3AirportID&VarType=Num&VarDesc=Div3AirportSeqID&VarType=Num&VarDesc=Div3WheelsOn&VarType=Char&VarDesc=Div3TotalGTime&VarType=Num&VarDesc=Div3LongestGTime&VarType=Num&VarDesc=Div3WheelsOff&VarType=Char&VarDesc=Div3TailNum&VarType=Char&VarDesc=Div4Airport&VarType=Char&VarDesc=Div4AirportID&VarType=Num&VarDesc=Div4AirportSeqID&VarType=Num&VarDesc=Div4WheelsOn&VarType=Char&VarDesc=Div4TotalGTime&VarType=Num&VarDesc=Div4LongestGTime&VarType=Num&VarDesc=Div4WheelsOff&VarType=Char&VarDesc=Div4TailNum&VarType=Char&VarDesc=Div5Airport&VarType=Char&VarDesc=Div5AirportID&VarType=Num&VarDesc=Div5AirportSeqID&VarType=Num&VarDesc=Div5WheelsOn&VarType=Char&VarDesc=Div5TotalGTime&VarType=Num&VarDesc=Div5LongestGTime&VarType=Num&VarDesc=Div5WheelsOff&VarType=Char&VarDesc=Div5TailNum&VarType=Char".format(YEAR, MONTH)

   url='https://www.transtats.bts.gov/DownLoad_Table.asp?Table_ID=236&Has_Group=3&Is_Zipped=0'
   filename = os.path.join(destdir, "{}{}.zip".format(YEAR, MONTH))
   with open(filename, "wb") as fp:
     response = urlopen(url, PARAMS)
     fp.write(response.read())
   logging.debug("{} saved".format(filename))
   return filename

def zip_to_csv(filename, destdir):
   zip_ref = zipfile.ZipFile(filename, 'r')
   cwd = os.getcwd()
   os.chdir(destdir)
   zip_ref.extractall()
   os.chdir(cwd)
   csvfile = os.path.join(destdir, zip_ref.namelist()[0])
   zip_ref.close()
   logging.info("Extracted {}".format(csvfile))
   return csvfile


class DataUnavailable(Exception):
   def __init__(self, message):
      self.message = message

class UnexpectedFormat(Exception):
   def __init__(self, message):
      self.message = message

def verify_ingest(csvfile):
   expected_header = 'FL_DATE,UNIQUE_CARRIER,AIRLINE_ID,CARRIER,FL_NUM,ORIGIN_AIRPORT_ID,ORIGIN_AIRPORT_SEQ_ID,ORIGIN_CITY_MARKET_ID,ORIGIN,DEST_AIRPORT_ID,DEST_AIRPORT_SEQ_ID,DEST_CITY_MARKET_ID,DEST,CRS_DEP_TIME,DEP_TIME,DEP_DELAY,TAXI_OUT,WHEELS_OFF,WHEELS_ON,TAXI_IN,CRS_ARR_TIME,ARR_TIME,ARR_DELAY,CANCELLED,CANCELLATION_CODE,DIVERTED,DISTANCE'

   with open(csvfile, 'r') as csvfp:
      firstline = csvfp.readline().strip()
      if (firstline != expected_header):
         os.remove(csvfile)
         msg = 'Got header={}, but expected={}'.format(
                             firstline, expected_header)
         logging.error(msg)
         raise UnexpectedFormat(msg)

      if next(csvfp, None) == None:
         os.remove(csvfile)
         msg = ('Received a file from BTS that has only the header and no content')
         raise DataUnavailable(msg)


def remove_quotes_comma(csvfile, year, month):
 '''
     returns output_csv_file or raises DataUnavailable exception
 '''
 try:
   outfile = os.path.join(os.path.dirname(csvfile),
                          '{}{}.csv'.format(year, month))
   with open(csvfile, 'r') as infp:
     with open(outfile, 'w') as outfp:
        for line in infp:
           outline = line.rstrip().rstrip(',')
           outline = remove_quote(outline)
           outfp.write(outline)
           outfp.write('\n')
   logging.debug('Ingested {} ...'.format(outfile))
   return outfile
 finally:
   logging.debug("... removing {}".format(csvfile))
   os.remove(csvfile)

def upload(csvfile, bucketname, blobname):
   client = storage.Client()
   bucket = client.get_bucket(bucketname)
   blob = Blob(blobname, bucket)
   blob.upload_from_filename(csvfile)
   gcslocation = 'gs://{}/{}'.format(bucketname, blobname)
   logging.info('Uploaded {} ...'.format(gcslocation))
   return gcslocation

def ingest(year, month, bucket):
   '''
   ingest flights data from BTS website to Google Cloud Storage
   return cloud-storage-blob-name on success.
   raises DataUnavailable if this data is not on BTS website
   '''
   tempdir = tempfile.mkdtemp(prefix='ingest_flights')
   try:
      zipfile = download(year, month, tempdir)
      bts_csv = zip_to_csv(zipfile, tempdir)
      csvfile = remove_quotes_comma(bts_csv, year, month)
      verify_ingest(csvfile)
      gcsloc = 'flights/raw/{}'.format(os.path.basename(csvfile))
      return upload(csvfile, bucket, gcsloc)
   finally:
      logging.debug('Cleaning up by removing {}'.format(tempdir))
      shutil.rmtree(tempdir)

def next_month(bucketname):
   '''
     Finds which months are on GCS, and returns next year,month to download
   '''
   client = storage.Client()
   bucket = client.get_bucket(bucketname)
   blobs  = list(bucket.list_blobs(prefix='flights/raw/'))
   files = [blob.name for blob in blobs if 'csv' in blob.name] # csv files only
   lastfile = os.path.basename(files[-1])
   logging.debug('The latest file on GCS is {}'.format(lastfile))
   year = lastfile[:4]
   month = lastfile[4:6]
   return compute_next_month(year, month)

def compute_next_month(year, month):
   dt = datetime.datetime(int(year), int(month), 15) # 15th of month
   dt = dt + datetime.timedelta(30) # will always go to next month
   logging.debug('The next month is {}'.format(dt))
   return '{}'.format(dt.year), '{:02d}'.format(dt.month)
  
if __name__ == '__main__':
   import argparse
   parser = argparse.ArgumentParser(description='ingest flights data from BTS website to Google Cloud Storage')
   parser.add_argument('--bucket', help='GCS bucket to upload data to', required=True)
   parser.add_argument('--year', help='Example: 2015.  If not provided, defaults to getting next month')
   parser.add_argument('--month', help='Specify 01 for January. If not provided, defaults to getting next month')

   try:
      logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
      args = parser.parse_args()
      if args.year is None or args.month is None:
         year, month = next_month(args.bucket)
      else:
         year = args.year
         month = args.month
      logging.debug('Ingesting year={} month={}'.format(year, month))
      gcsfile = ingest(year, month, args.bucket)
      logging.info('Success ... ingested to {}'.format(gcsfile))
   except DataUnavailable as e:
      logging.info('Try again later: {}'.format(e.message))

