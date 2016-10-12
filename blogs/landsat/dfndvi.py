#!/usr/bin/env python

import apache_beam as beam
import ndvi

class SceneInfo:
   def __init__ (self, line):
      self.SCENE_ID, self.SPACECRAFT_ID, self.SENSOR_ID, self.DATE_ACQUIRED, self.COLLECTION_NUMBER, self.COLLECTION_CATEGORY,self.DATA_TYPE, self.WRS_PATH, self.WRS_ROW, self.CLOUD_COVER, self.NORTH_LAT, self.SOUTH_LAT, self.WEST_LON, self.EAST_LON, self.TOTAL_SIZE, self.BASE_URL = line.split(',')
   
   def contains(self, lat, lon):
      return (lat > self.SOUTH_LAT and lat < self.NORTH_LAT and lon > self.WEST_LON and lon < self.EAST_LON)


def filterScenes(line, lat, lon):
   scene = SceneInfo(line)
   if scene.contains(lat, lon):
      yield scene.__dict__ 


if __name__ == '__main__':
   p = beam.Pipeline('DirectPipelineRunner')
   index_file = 'smindex.txt'  # gs://gcp-public-data-landsat/index.csv.gz
   output_file = 'output.txt'

   # Madagascar
   lat =  -19
   lon =   47

   # Read a file containing names, add a greeting to each name, and write to a file.
   (p
      | 'read_index' >> beam.Read(beam.io.TextFileSource(index_file))
      | 'filter_scenes' >> beam.FlatMap(lambda line: filterScenes(line, lat, lon) )
      | 'write' >> beam.io.textio.WriteToText(output_file)
   )

   p.run()

