#!/usr/bin/env python

from pyresample import geometry
from satpy.scene import Scene
from datetime import datetime
import numpy as np
import subprocess
import shutil,os
import satpy

outdir = 'image'
shutil.rmtree(outdir, ignore_errors=True)
os.mkdir(outdir)

def copy_fromgcs(gcs_pattern, tmpdir):
   from os import listdir
   from os.path import isfile, join
   shutil.rmtree(tmpdir, ignore_errors=True)
   os.makedirs(tmpdir)
   copy_command = 'gsutil cp {} {}'.format(gcs_pattern, tmpdir)
   subprocess.check_call(copy_command.split())
   onlyfiles = [f for f in listdir(tmpdir) if isfile(join(tmpdir, f))]
   return join(tmpdir, onlyfiles[0])

def plot_image(ncfilename, outfile, clat, clon):
    from netCDF4 import Dataset
    import matplotlib
    matplotlib.use('Agg') # headless display
    import matplotlib.pyplot as plt
    from mpl_toolkits.basemap import Basemap
    import numpy as np
    import pyresample
    with Dataset(ncfilename, 'r') as nc:
        # print(nc.variables.keys())
        rad = nc.variables['Rad'][:]
        # See http://www.goes-r.gov/products/ATBDs/baseline/Imagery_v2.0_no_color.pdf
        ref = (rad * np.pi * 0.3) / 663.274497
        ref = np.minimum( np.maximum(ref, 0.0), 1.0 )

        # plotting
        fig = plt.figure()
        plt.imshow(ref, vmin=0.0, vmax=1.0, cmap='Greys_r')
        fig.savefig(outfile)
        plt.close('all')
        return outfile
    return None


with open('MARIA.csv', 'r') as ifp:
 for line in ifp:
   fields = line.split(',')
   # print '***'.join(fields)
   dt = datetime.strptime(fields[6], '%Y-%m-%d %H:%M:%S')
   dayno = dt.timetuple().tm_yday
   lat = float(fields[8])
   lon = float(fields[9])

   # copy 11-micron band (C14) to local disk
   # See: https://www.goes-r.gov/education/ABI-bands-quick-info.html
   gcs_pattern = 'gs://gcp-public-data-goes-16/ABI-L1b-RadF/{0}/{1:03d}/{2:02d}/*C14*_s{0}{1:03d}{2:02d}00*'.format(dt.year, dayno, dt.hour)
   local_file = copy_fromgcs(gcs_pattern, 'tmpdir')

   # create image
   jpgfile = '{}/ir_{}{}{}.jpg'.format(outdir, dt.year, dayno, dt.hour)
   jpgfile = plot_image(local_file, jpgfile, lat, lon)

   # cleanup
   shutil.rmtree('tmpdir')
   exit
