#!/usr/bin/env python

"""
Copyright Google Inc. 2017
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

def copy_fromgcs(gcs_pattern, destdir):
   import os.path
   import subprocess
   import logging
   list_command = 'gsutil ls {}'.format(gcs_pattern)
   filenames = subprocess.check_output(list_command.split())
   filenames = str(filenames).split()
   if len(filenames) > 0:
      copy_command = 'gsutil cp {} {}'.format(filenames[0], destdir)
      subprocess.check_call(copy_command.split())
      basename = os.path.basename(filenames[0])
      logging.info('{} caused download of {}'.format(copy_command, basename))
      return os.path.join(destdir, basename)
   return None

def copy_togcs(localfile, gcs_path):
   import subprocess, logging
   copy_command = 'gsutil cp {} {}'.format(localfile, gcs_path)
   subprocess.check_call(copy_command.split())
   logging.info('{} uploaded to {}'.format(localfile, gcs_path))

def crop_image(nc, data, clat, clon):
   import logging
   import numpy as np
   from pyproj import Proj
   import pyresample as pr

   # output grid centered on clat, clon in equal-lat-lon 
   lats = np.arange(clat-10,clat+10,0.01) # approx 1km resolution, 2000km extent
   lons = np.arange(clon-10,clon+10,0.01) # approx 1km resolution, 2000km extent
   lons, lats = np.meshgrid(lons, lats)
   new_grid = pr.geometry.GridDefinition(lons=lons, lats=lats)

   # Subsatellite_Longitude is where the GEO satellite is 
   lon_0 = nc.variables['nominal_satellite_subpoint_lon'][0]
   ht_0 = nc.variables['nominal_satellite_height'][0] * 1000 # meters
   x = nc.variables['x'][:] * ht_0 #/ 1000.0
   y = nc.variables['y'][:] * ht_0 #/ 1000.0
   nx = len(x)
   ny = len(y)
   max_x = x.max(); min_x = x.min(); max_y = y.max(); min_y = y.min()
   half_x = (max_x - min_x) / nx / 2.
   half_y = (max_y - min_y) / ny / 2.
   extents = (min_x - half_x, min_y - half_y, max_x + half_x, max_y + half_y)
   old_grid = pr.geometry.AreaDefinition('geos','goes_conus','geos', 
       {'proj':'geos', 'h':str(ht_0), 'lon_0':str(lon_0) ,'a':'6378169.0', 'b':'6356584.0'},
       nx, ny, extents)

   # now do remapping
   logging.info('Remapping from {}'.format(old_grid))
   return pr.kd_tree.resample_nearest(old_grid, data, new_grid, radius_of_influence=50000)

def plot_image(ncfilename, outfile, clat, clon):
    import matplotlib, logging
    matplotlib.use('Agg') # headless display
    import numpy as np
    from netCDF4 import Dataset
    import matplotlib.pyplot as plt
    
    with Dataset(ncfilename, 'r') as nc:
        rad = nc.variables['Rad'][:]
        # See http://www.goes-r.gov/products/ATBDs/baseline/Imagery_v2.0_no_color.pdf
        ref = (rad * np.pi * 0.3) / 663.274497
        ref = np.minimum( np.maximum(ref, 0.0), 1.0 )

        # crop to area of interest
        ref = crop_image(nc, ref, clat, clon)
        
        # do gamma correction to stretch the values
        ref = np.sqrt(ref)

        # plotting to jpg file
        fig = plt.figure()
        plt.imsave(outfile, ref, vmin=0.0, vmax=1.0, cmap='gist_ncar_r') # or 'Greys_r' without color
        plt.close('all')
        logging.info('Created {}'.format(outfile))
        return outfile
    return None

def goes_to_jpeg(line, outdir):
    from datetime import datetime
    import os, shutil, tempfile, subprocess, logging

    fields = line.split(',')
    dt = datetime.strptime(fields[6], '%Y-%m-%d %H:%M:%S')
    dayno = dt.timetuple().tm_yday
    lat = float(fields[8])
    lon = float(fields[9])

    # copy 11-micron band (C14) to local disk
    # See: https://www.goes-r.gov/education/ABI-bands-quick-info.html
    gcs_pattern = 'gs://gcp-public-data-goes-16/ABI-L1b-RadF/{0}/{1:03d}/{2:02d}/*C14*_s{0}{1:03d}{2:02d}*'.format(dt.year, dayno, dt.hour)
    tmpdir = tempfile.mkdtemp()
    local_file = copy_fromgcs(gcs_pattern, tmpdir)

    # create image in temporary dir, then move over
    jpgfile = '{}/ir_{}{}{}.jpg'.format(tmpdir, dt.year, dayno, dt.hour)
    jpgfile = plot_image(local_file, jpgfile, lat, lon)

    # move over
    if len(outdir) > 3 and outdir[:3] == 'gs:':
        jpgfile = copy_togcs(jpgfile, '{}/{}'.format(outdir, os.path.basename(jpgfile)))
    else:
        subprocess.check_call(['mv', jpgfile, outdir])
        jpgfile = '{}/{}'.format(outdir, os.path.basename(jpgfile))

    # cleanup
    shutil.rmtree(tmpdir)
    logging.info('Created {} from {}'.format(jpgfile, gcs_pattern))
    return jpgfile


