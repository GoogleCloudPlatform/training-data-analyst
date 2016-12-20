#!/usr/bin/env python

def write_geotiff(predictions, outfilename):
  '''
      predictions should be a np.array([nrows, ncols], dtype=np.float32)
      return (lineno, linedata, featnames)
      where linedata is a 2D array with first dimension being feature# and second dimension column in image 
  '''  
  import osgeo.gdal as gdal
  import struct
  import tempfile
  import os
  import subprocess
  
  # The gdal library can not read from CloudStorage, so this class downloads the data to local VM
  class LandsatReader():
   def __init__(self, gsfile, destdir='./'):
      self.gsfile = gsfile
      self.dest = os.path.join(destdir, os.path.basename(self.gsfile))
      if os.path.exists(self.dest):
        print 'Using already existing {}'.format(self.dest)
      else:
        print 'Getting {0} to {1} '.format(self.gsfile, self.dest)
        ret = subprocess.check_call(['gsutil', 'cp', self.gsfile, self.dest])
      self.dataset = gdal.Open( self.dest, gdal.GA_ReadOnly )
   def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
      os.remove( self.dest ) # cleanup  
   def ds(self):
      return self.dataset

  # use the original Landcover file to get the headers etc. correct
  input_dir = 'gs://mdh-test/landsat-ml/'
  filename = os.path.join(input_dir, 'mcd12-labels.tif')
  reader = LandsatReader(filename)
  inds = reader.ds()
  inband = inds.GetRasterBand(1) 
  tmpfilename = os.path.join(tempfile.gettempdir(), 'landcover.TIF')
  driver = gdal.GetDriverByName('GTiff')
  outdtype = gdal.GDT_Float32
  outds = driver.Create(tmpfilename, inds.RasterXSize, inds.RasterYSize, 1, outdtype)
  outds.SetGeoTransform(inds.GetGeoTransform())
  outds.SetProjection(inds.GetProjection())

  # fill in data, and write out the file line-by-line
  ncols = inband.XSize
  nrows = inband.YSize
  packformat = 'f' * ncols
  for line in xrange(0, nrows):
    if line % 10 == 0:
      print "line_{} written ...".format(line)
    outline = struct.pack(packformat, *(predictions[line]))
    outds.GetRasterBand(1).WriteRaster(0, line, ncols, 1, outline, buf_xsize=ncols, buf_ysize=1, buf_type=outdtype)
    del outline
  outds = None # close
  ret = subprocess.check_call(['gsutil', 'mv', tmpfilename, outfilename])
  print 'Wrote {0} ...'.format(outfilename)
 
def set_pixel_from(pixel_predictions, s):
  row, col = s['key'].split(',')
  newval = int(s['label'])
  pixel_predictions[row,col] = newval
    
def create_downscaled():
  import os
  import numpy as np
  import apache_beam as beam
  import google.cloud.ml as ml
  import google.cloud.ml.io as io
  import google.cloud.ml.features as features
  import json
  from StringIO import StringIO

  BUCKET = 'cloud-training-demos-ml'
  PROJECT = 'cloud-training-demos'
  #RUNNER = 'DirectPipelineRunner'
  #INPUT = '/content/training-data-analyst/blogs/landsat-ml/landcover_eval/eval*'
  RUNNER = 'DataflowPipelineRunner'
  INPUT = 'gs://cloud-training-demos-ml/landcover/prediction/eval*'
  
  pipeline = beam.Pipeline(argv=['--project', PROJECT,
                               '--runner', RUNNER,
                               '--job_name', 'landcoverwrite',
                               '--extra_package', ml.sdk_location,
                               '--max_num_workers', '10',
                               '--autoscaling_algorithm', 'THROUGHPUT_BASED',
                               '--worker_machine_type', 'n1-standard-4',
                               '--save_main_session', 'True',
                               '--setup_file', './preproc/setup.py',  # for gdal installation on the cloud -- see CUSTOM_COMMANDS in setup.py
                               '--staging_location', 'gs://{0}/landcover/staging'.format(BUCKET),
                               '--temp_location', 'gs://{0}/landcover/temp'.format(BUCKET)])
        
  print ml.sdk_location
  imgsize = 16384 # of full image
  pixel_predictions = np.zeros(shape=(imgsize, imgsize), dtype=np.float32)
  print 'in-memory array created ...'
  
  (pipeline 
     | beam.Read(beam.io.TextFileSource(INPUT))
     | beam.Map(lambda line: eval(line)) # struct
     | beam.Map(lambda s: set_pixel_from(pixel_predictions, s))
  ) #
   
  pipeline.run()
  write_geotiff(pixel_predictions, 'gs://cloud-training-demos-ml/landcover/prediction/landcover.TIF')

if __name__ == '__main__':
  create_downscaled()
