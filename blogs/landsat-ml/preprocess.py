# a Python generator that packs all the training data line-by-line
def get_next_line(SMALL_SAMPLE):
  '''
      return (lineno, linedata, featnames)
      where linedata is a 2D array with first dimension being feature# and second dimension column in image 
  '''  
  import osgeo.gdal as gdal
  import struct
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

  # open all the necessary files
  input_dir = 'gs://mdh-test/landsat-ml/'
  featnames = ['b{}'.format(band) for band in xrange(1,8)] # 8
  filenames = [os.path.join(input_dir, 'landsat8-{}.tif'.format(band)) for band in featnames]
  filenames.append(os.path.join(input_dir, 'srtm-elevation.tif')); featnames.append('elev')
  filenames.append(os.path.join(input_dir, 'mcd12-labels.tif')); featnames.append('landcover')
  readers = [LandsatReader(filename) for filename in filenames]
  bands = [reader.ds().GetRasterBand(1) for reader in readers] 
  print "Opened ", filenames
      
  # read one row of each the images and yield them
  ncols = bands[0].XSize
  nrows = bands[0].YSize
  if SMALL_SAMPLE:
    nrows_to_read = 200
    ncols_to_read = 1000
  else:
    nrows_to_read = nrows
    ncols_to_read = ncols
  print "Reading ", nrows_to_read, "x", ncols_to_read, " from ", nrows, 'x', ncols, ' images corresponding to ', featnames
  packformat = 'f' * ncols
  for line in xrange(0, nrows_to_read):
        line_data = [struct.unpack(packformat, band.ReadRaster(0, line, ncols, 1, ncols, 1, gdal.GDT_Float32)) for band in bands]
        yield (line, (line_data, featnames, ncols_to_read))
      
def get_features_from_line(args):
  '''
      return (1, dict)  or (0, dict)
      where the first number is 1 or 0 depending on whether this row belongs to training (1)
      or eval (0) partition.
      dict is the set of features formed from pixels from all the bands
  ''' 
  # line, [(line_data, featnames, ncols_to_read)] = args
  line = args[0]
  for (line_data, featnames, ncols_to_read) in args[1]:
    if line_data:
       for col in xrange(0, ncols_to_read):
          featdict = {'rowcol': '{},{}'.format(line,col)}
          for f in xrange(0, len(featnames)):
            featdict[featnames[f]] = line_data[f][col]
          featdict['landcover'] = '{}'.format(int(featdict['landcover']+0.5))
          yield ( 0 if (line+col)%3==0 else 1, featdict )    # 1/3 are eval

def get_partition(group_and_featdict, nparts):
  (is_train, featdict) = group_and_featdict
  return is_train # 0 or 1

def get_featdict(group_and_featdict):
  (is_train, featdict) = group_and_featdict
  return featdict

def run_preprocessing(BUCKET=None, PROJECT=None):
  import os
  import numpy as np
  import apache_beam as beam
  import google.cloud.ml as ml
  import google.cloud.ml.io as io
  import google.cloud.ml.features as features

  # small sample locally; full dataset on cloud
  if BUCKET is None or PROJECT is None:
    SMALL_SAMPLE = True
    OUTPUT_DIR = './landcover_preproc'
    RUNNER = 'DirectPipelineRunner'
  else:
    SMALL_SAMPLE = False
    OUTPUT_DIR = 'gs://{0}/landcoverml/preproc'.format(BUCKET)
    RUNNER = 'DataflowPipelineRunner'
  #
  
  pipeline = beam.Pipeline(argv=['--project', PROJECT,
                               '--runner', RUNNER,
                               '--job_name', 'landcover',
                               '--extra_package', ml.sdk_location,
                               '--max_num_workers', '50',
                               '--no_save_main_session', 'True',  # to prevent pickling and uploading Datalab itself!
                               '--setup_file', './preproc/setup.py',  # for gdal installation on the cloud -- see CUSTOM_COMMANDS in setup.py
                               '--staging_location', 'gs://{0}/landcoverml/staging'.format(BUCKET),
                               '--temp_location', 'gs://{0}/landcoverml/temp'.format(BUCKET)])
        
  print ml.sdk_location
  
  (evalg, traing) = (pipeline 
     | beam.Create([SMALL_SAMPLE]) # make the generator function like a source
     | beam.FlatMap(get_next_line) # (line, (line_data, featnames, ncols_to_read))
     | beam.GroupByKey() # line, [(line_data, featnames, ncols_to_read)]
     | beam.FlatMap(get_features_from_line) # (is_train, featdict)
     | beam.Partition(get_partition, 2)
  )  # eval, train both contain (is_train, featdict)
  eval = evalg | 'eval_features' >> beam.Map(get_featdict)
  train = traing | 'train_features' >> beam.Map(get_featdict)
  
  class LandcoverFeatures(object):
    key = features.key('rowcol')
    landcover = features.target('landcover').discrete()  # classification problem
    inputbands = [
      features.numeric('b1').scale(),
      features.numeric('b2').scale(),
      features.numeric('b3').scale(),
      features.numeric('b4').scale(),
      features.numeric('b5').scale(),
      features.numeric('b6').scale(),
      features.numeric('b7').scale(),
      #features.numeric('el').discretize(buckets=[1,5001,50], sparse=True),  # elevation
    ]
  feature_set = LandcoverFeatures()
  (metadata, train_features, eval_features) = ((train, eval) |
   'Preprocess' >> ml.Preprocess(feature_set, input_format='json'))
  (metadata
     | 'SaveMetadata'
     >> io.SaveMetadata(os.path.join(OUTPUT_DIR, 'metadata.yaml')))
  (train_features
     | 'WriteTraining'
     >> io.SaveFeatures(os.path.join(OUTPUT_DIR, 'features_train')))
  (eval_features
     | 'WriteEval'
     >> io.SaveFeatures(os.path.join(OUTPUT_DIR, 'features_eval')))
  pipeline.run()

if __name__ == '__main__':
   run_preprocessing(BUCKET='cloud-training-demos-ml', PROJECT='cloud-training-demos')
