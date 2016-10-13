#!/usr/bin/env python

import apache_beam as beam
import numpy as np
import ndvi

class SceneInfo:
   def __init__ (self, line):
      self.SCENE_ID, self.SPACECRAFT_ID, self.SENSOR_ID, self.DATE_ACQUIRED, self.COLLECTION_NUMBER, self.COLLECTION_CATEGORY,self.DATA_TYPE, self.WRS_PATH, self.WRS_ROW, self.CLOUD_COVER, self.NORTH_LAT, self.SOUTH_LAT, self.WEST_LON, self.EAST_LON, self.TOTAL_SIZE, self.BASE_URL = line.split(',')
      try:
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


def filterScenes(line, lat, lon):
   scene = SceneInfo(line)
   if scene.contains(lat, lon):
      #closeness = scene.distanceFrom(lat, lon)  # in deg (typically around 2)
      #cloudy = 0.01*scene.CLOUD_COVER  # 0-1
      #yield cloudy, scene
      yield scene.__dict__


if __name__ == '__main__':
   p = beam.Pipeline('DirectPipelineRunner')
   index_file = 'smindex.txt'  # gs://gcp-public-data-landsat/index.csv.gz
   output_file = 'output.txt'

   # Madagascar
   lat =  -19
   lon =   47

   # 80.30033,77.80218,-17.92835,-3.38792
   lat = 78.0
   lon = -10.0

   # Read a file containing names, add a greeting to each name, and write to a file.
   (p
      | 'read_index' >> beam.Read(beam.io.TextFileSource(index_file))
      | 'filter_scenes' >> beam.FlatMap(lambda line: filterScenes(line, lat, lon) )
      | 'write' >> beam.io.textio.WriteToText(output_file)
   )

   p.run()

