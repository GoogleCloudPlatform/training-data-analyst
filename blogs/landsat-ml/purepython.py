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
     

 
if __name__ == '__main__':

  imgavg = 0
  for args in get_next_line(False):
     line = args[0]
     (line_data, featnames, ncols_to_read) = args[1]
     if line_data:
        total = 0
        for col in xrange(0, ncols_to_read):
           for f in xrange(0, len(featnames)):
               total += line_data[f][col]
        avg = total / ncols_to_read
        if line % 100 == 0:
           print line, avg
        imgavg += avg
  print imgavg
