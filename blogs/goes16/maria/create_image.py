#!/usr/bin/env python

from pyresample import geometry
from satpy.scene import Scene
from datetime import datetime
import subprocess
import satpy
import shutil,os

tmpdir = 'tmp'
outdir = 'image'
shutil.rmtree(tmpdir)
os.mkdirs(outdir)
with open('MARIA.csv', 'r') as ifp:
 for line in ifp:
   fields = line.split(',')
   # print '***'.join(fields)
   dt = datetime.strptime(fields[6], '%Y-%m-%d %H:%M:%S')
   dayno = dt.timetuple().tm_yday
   lat = float(fields[8])
   lon = float(fields[9])

   # make up the grid to resample into
   lats = np.arange(lat-1,lat+1,0.01) # approx 1km resolution, 200km extent
   lons = np.arange(lon-1,lon+1,0.01) # approx 1km resolution, 200km extent
   lons, lats = np.meshgrid(lons, lats)
   grid_def = geometry.GridDefinition(lons=lons, lats=lats)

   # copy 11-micron band (C14) to local disk
   # See: https://www.goes-r.gov/education/ABI-bands-quick-info.html
   gcs_pattern = 'gs://gcp-public-data-goes-16/ABI-L1b-RadF/{0}/{1}/{2}/*C14*_s{0}{1}{2}00*'.format(dt.year, dayno, dt.hour)
   outfile = '{}/tmp_{}{}{}'.format(tmpdir, dt.year, dayno, dt.hour)
   os.mkdirs(tmpdir)
   copy_command = 'gsutil cp -m {} {}'.format(all_files, outfile)
   subprocess.check_call(copy_command.split())

   # create image
   scene = Scene(filenames=outfile, reader="abi_l1b")
   scene.resample(grid_def)
   outfile = '{}/ir_{}{}{}.png'.format(outdir, dt.year, dayno, dt.hour)
   scene.save_dataset('overview', outfile)

   # cleanup
   shutil.rmtree(tmpdir)
   exit
