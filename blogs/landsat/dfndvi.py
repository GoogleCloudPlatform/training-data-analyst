#!/usr/bin/env python

import apache_beam as beam
import numpy as np
import datetime
import ndvi

class SceneInfo:
   def __init__ (self, line):
      try:
        self.SCENE_ID, self.SPACECRAFT_ID, self.SENSOR_ID, self.DATE_ACQUIRED, self.COLLECTION_NUMBER, self.COLLECTION_CATEGORY,self.DATA_TYPE, self.WRS_PATH, self.WRS_ROW, self.CLOUD_COVER, self.NORTH_LAT, self.SOUTH_LAT, self.WEST_LON, self.EAST_LON, self.TOTAL_SIZE, self.BASE_URL = line.split(',')

        self.DATE_ACQUIRED = datetime.datetime.strptime(self.DATE_ACQUIRED, '%Y-%m-%d')
        self.NORTH_LAT = float(self.NORTH_LAT)
        self.SOUTH_LAT = float(self.SOUTH_LAT)
        self.WEST_LON = float(self.WEST_LON)
        self.EAST_LON = float(self.EAST_LON)
        self.CLOUD_COVER = float(self.CLOUD_COVER)
      except:
        print "WARNING! format error on {", line, "}"        

   def contains(self, lat, lon):
      return (lat > self.SOUTH_LAT) and (lat < self.NORTH_LAT) and (lon > self.WEST_LON) and (lon < self.EAST_LON)

   def distanceFrom(self, lat, lon):
      return np.sqrt(np.square(lat - (self.SOUTH_LAT + self.NORTH_LAT)/2) + 
                     np.square(lon - (self.WEST_LON + self.EAST_LON)/2))

   def timeDiff(self, date):
      return (self.DATE_ACQUIRED - date).days


def filterScenes(line, lat, lon, date):
   scene = SceneInfo(line)
   if scene.contains(lat, lon) and np.abs(scene.timeDiff(date)) < 4:
      yield scene

def clearest(scenes):
   if scenes:
      return min(scenes, key=lambda s: s.CLOUD_COVER)
   else:
      return None

if __name__ == '__main__':
   p = beam.Pipeline('DirectPipelineRunner')    # DataflowPipelineRunner
   index_file = 'gs://gcp-public-data-landsat/index.csv.gz'
   output_file = 'output.txt'

   # Madagascar
   lat =  -19
   lon =   47
   date = datetime.datetime(2016, 7, 15)

   # Read the index file and find the best look
   scenes = (p
      | 'read_index' >> beam.Read(beam.io.TextFileSource(index_file))
      | 'filter_scenes' >> beam.FlatMap(lambda line: filterScenes(line, lat, lon, date) )
      | 'least_cloudy' >> beam.CombineGlobally(clearest)
   )

   # write out info about scene
   scenes | beam.Map(lambda scene: scene.__dict__) | 'scene_info' >> beam.io.textio.WriteToText(output_file)

   # compute ndvi on scene
   scenes | 'compute_ndvi' >> beam.Map(lambda scene: ndvi.computeNdvi(scene.BASE_URL, '.'))

   p.run()

