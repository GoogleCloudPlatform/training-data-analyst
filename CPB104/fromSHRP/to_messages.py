#!/usr/bin/env python

import datetime



INPUT='raw.csv'
OUTPUT='messages.csv'

def notify(line, colnames):
   # DATE,TIME,STATION_ID,LATITUDE,LONGITUDE,DISTRICT,FREEWAY_ID,FREEWAY_DIR,STATION_TYPE,LENGTH,SAMPLES,PCT_OBSERVED,FLOW,OCC,SPEED,LANE_1_SAMPLES,LANE_1_FLOW,LANE_1_OCC,LANE_1_SPEED,LANE_1_OBS,LANE_2_SAMPLES,LANE_2_FLOW,LANE_2_OCC,LANE_2_SPEED,LANE_2_OBS,LANE_3_SAMPLES,LANE_3_FLOW,LANE_3_OCC,LANE_3_SPEED,LANE_3_OBS,LANE_4_SAMPLES,LANE_4_FLOW,LANE_4_OCC,LANE_4_SPEED,LANE_4_OBS,LANE_5_SAMPLES,LANE_5_FLOW,LANE_5_OCC,LANE_5_SPEED,LANE_5_OBS,LANE_6_SAMPLES,LANE_6_FLOW,LANE_6_OCC,LANE_6_SPEED,LANE_6_OBS,LANE_7_SAMPLES,LANE_7_FLOW,LANE_7_OCC,LANE_7_SPEED,LANE_7_OBS,LANE_8_SAMPLES,LANE_8_FLOW,LANE_8_OCC,LANE_8_SPEED,LANE_8_OBS

   incols = line.strip().split(',')
   indict = {}
   for name, value in zip(colnames, incols):
     indict[name] = value
   
   outcols = []
   INTIME_FORMAT = '%d/%m/%Y %H:%M:%S'
   intime = indict['DATE'] + ' ' + indict['TIME']
   intime = datetime.datetime.strptime(intime, INTIME_FORMAT)
   outcols.append( str(intime) )

   if str(intime) > '2008-01':
      exit(0)  # only one month

   for colname in 'LATITUDE,LONGITUDE,FREEWAY_ID,FREEWAY_DIR'.split(','):
      outcols.append(indict[colname])
   
   for laneno in xrange(1,9):
       lane = str(laneno)
       samples = indict['LANE_' + lane + '_SAMPLES']
       occ = indict['LANE_' + lane + '_OCC']
       speed = indict['LANE_' + lane + '_SPEED']
       obs = indict['LANE_' + lane + '_OBS']
       if len(samples) > 0 and len(occ) > 0 and len(speed) > 0 and len(obs) > 0:
          lanemsg = list(outcols) # copy
          lanemsg.append(lane)
          # lanemsg.append(samples)  # number of measurements
          # lanemsg.append(occ)      # number of occupants
          lanemsg.append(speed)    # speed
          # lanemsg.append(obs)
          print ','.join(lanemsg)


if __name__ == '__main__':
   with open(INPUT, 'r') as ifp:
      print 'TIMESTAMP,LATITUDE,LONGITUDE,FREEWAY_ID,FREEWAY_DIR,LANE,SPEED'
      colnames = ifp.readline().strip().split(',')
      for line in ifp:
         notify(line, colnames)
