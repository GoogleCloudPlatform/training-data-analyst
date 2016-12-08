#!/usr/bin/env python

import apache_beam as beam
import csv

def addtimezone(lat, lon):
   try:
      import timezonefinder
      tf = timezonefinder.TimezoneFinder()
      return (lat, lon, tf.timezone_at(lng=float(lon), lat=float(lat)))
      #return (lat, lon, 'America/Los_Angeles') # FIXME
   except ValueError:
      return (lat, lon, 'TIMEZONE') # header

def as_utc(date, hhmm, tzone):
   try:
      if len(hhmm) > 0 and tzone is not None:
         import datetime, pytz
         loc_tz = pytz.timezone(tzone)
         loc_dt = loc_tz.localize(datetime.datetime.strptime(date,'%Y-%m-%d'), is_dst=False)
         # can't just parse hhmm because the data contains 2400 and the like ...
         loc_dt += datetime.timedelta(hours=int(hhmm[:2]), minutes=int(hhmm[2:]))
         utc_dt = loc_dt.astimezone(pytz.utc)
         return utc_dt.strftime('%Y-%m-%d %H:%M:%S'), loc_dt.utcoffset().total_seconds()
      else:
         return '',0 # empty string corresponds to canceled flights
   except ValueError as e:
      print '{} {} {}'.format(date, hhmm, tzone)
      raise e

def add_24h_if_before(arrtime, deptime):
   import datetime
   if arrtime < deptime:
      adt = datetime.datetime.strptime(arrtime, '%Y-%m-%d %H:%M:%S')
      adt += datetime.timedelta(hours=24)
      return adt.strftime('%Y-%m-%d %H:%M:%S')
   else:
      return arrtime

def tz_correct(line, airport_timezones):
   fields = line.split(',')
   if fields[0] != 'FL_DATE' and len(fields) == 27:
      # convert all times to UTC
      dep_airport_id = fields[6]
      arr_airport_id = fields[10]
      dep_timezone = airport_timezones[dep_airport_id][2] 
      arr_timezone = airport_timezones[arr_airport_id][2]
      
      for f in [13, 14, 17]: #crsdeptime, deptime, wheelsoff
         fields[f], deptz = as_utc(fields[0], fields[f], dep_timezone)
      for f in [18, 20, 21]: #wheelson, crsarrtime, arrtime
         fields[f], arrtz = as_utc(fields[0], fields[f], arr_timezone)
      
      for f in [17, 18, 20, 21]:
         fields[f] = add_24h_if_before(fields[f], fields[14])

      fields.extend(airport_timezones[dep_airport_id])
      fields[-1] = str(deptz)
      fields.extend(airport_timezones[arr_airport_id])
      fields[-1] = str(arrtz)

      yield fields

def get_next_event(fields):
    if len(fields[14]) > 0:
       event = list(fields) # copy
       event.extend(['departed', fields[14]])
       for f in [16,17,18,19,21,22,25]:
          event[f] = ''  # not knowable at departure time
       yield event
    if len(fields[21]) > 0:
       event = list(fields)
       event.extend(['arrived', fields[21]])
       yield event

def create_row(fields):
    header = 'FL_DATE,UNIQUE_CARRIER,AIRLINE_ID,CARRIER,FL_NUM,ORIGIN_AIRPORT_ID,ORIGIN_AIRPORT_SEQ_ID,ORIGIN_CITY_MARKET_ID,ORIGIN,DEST_AIRPORT_ID,DEST_AIRPORT_SEQ_ID,DEST_CITY_MARKET_ID,DEST,CRS_DEP_TIME,DEP_TIME,DEP_DELAY,TAXI_OUT,WHEELS_OFF,WHEELS_ON,TAXI_IN,CRS_ARR_TIME,ARR_TIME,ARR_DELAY,CANCELLED,CANCELLATION_CODE,DIVERTED,DISTANCE,DEP_AIRPORT_LAT,DEP_AIRPORT_LON,DEP_AIRPORT_TZOFFSET,ARR_AIRPORT_LAT,ARR_AIRPORT_LON,ARR_AIRPORT_TZOFFSET,EVENT,NOTIFY_TIME'.split(',')

    featdict = {}
    for name, value in zip(header, fields):
        featdict[name] = value
    return featdict
 
def run(project, bucket):
   argv = [
      '--project={0}'.format(project),
      '--job_name=ch03timecorr',
      '--save_main_session',
      '--staging_location=gs://{0}/flights/staging/'.format(bucket),
      '--temp_location=gs://{0}/flights/temp/'.format(bucket),
      '--setup_file=./setup.py',
      '--runner=DataflowPipelineRunner'
   ]
   airports_filename = 'gs://{}/flights/airports/airports.csv.gz'.format(bucket)
   flights_raw_files = 'gs://{}/flights/raw/201501.csv'.format(bucket)
   flights_output = 'gs://{}/flights/tzcorr/all_flights'.format(bucket)
   events_output = '{}:flights.simevents'.format(project)

   pipeline = beam.Pipeline(argv=argv)
   
   airports = (pipeline 
      | 'airports:read' >> beam.Read(beam.io.TextFileSource(airports_filename))
      | 'airports:fields' >> beam.Map(lambda line: next(csv.reader([line])))
      | 'airports:tz' >> beam.Map(lambda fields: (fields[0], addtimezone(fields[21], fields[26])))
   )

   flights = (pipeline 
      | 'flights:read' >> beam.Read(beam.io.TextFileSource(flights_raw_files))
      | 'flights:tzcorr' >> beam.FlatMap(tz_correct, beam.pvalue.AsDict(airports))
   )

   (flights 
      | 'flights:tostring' >> beam.Map(lambda fields: ','.join(fields)) 
      | 'flights:out' >> beam.io.textio.WriteToText(flights_output)
   )

   events = flights | beam.FlatMap(get_next_event)

   schema = 'FL_DATE:date,UNIQUE_CARRIER:string,AIRLINE_ID:string,CARRIER:string,FL_NUM:string,ORIGIN_AIRPORT_ID:string,ORIGIN_AIRPORT_SEQ_ID:integer,ORIGIN_CITY_MARKET_ID:string,ORIGIN:string,DEST_AIRPORT_ID:string,DEST_AIRPORT_SEQ_ID:integer,DEST_CITY_MARKET_ID:string,DEST:string,CRS_DEP_TIME:datetime,DEP_TIME:datetime,DEP_DELAY:float,TAXI_OUT:float,WHEELS_OFF:datetime,WHEELS_ON:datetime,TAXI_IN:float,CRS_ARR_TIME:datetime,ARR_TIME:datetime,ARR_DELAY:float,CANCELLED:string,CANCELLATION_CODE:string,DIVERTED:string,DISTANCE:float,DEP_AIRPORT_LAT:float,DEP_AIRPORT_LON:float,DEP_AIRPORT_TZOFFSET:float,ARR_AIRPORT_LAT:float,ARR_AIRPORT_LON:float,ARR_AIRPORT_TZOFFSET:float,EVENT:string,NOTIFY_TIME:datetime'

   (events 
      | 'events:totablerow' >> beam.Map(lambda fields: create_row(fields)) 
      | 'events:out' >> beam.io.Write(beam.io.BigQuerySink(
                              events_output, schema=schema,
                              write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE,
                              create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED))
   )

   pipeline.run()

if __name__ == '__main__':
   run(project='cloud-training-demos', bucket='cloud-training-demos-ml')
