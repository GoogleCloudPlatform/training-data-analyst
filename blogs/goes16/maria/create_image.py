#!/usr/bin/env python

def copy_fromgcs(gcs_pattern, destdir):
   import os.path
   import subprocess
   list_command = 'gsutil ls {}'.format(gcs_pattern)
   filenames = subprocess.check_output(list_command.split())
   filenames = str(filenames).split()
   if len(filenames) > 0:
      copy_command = 'gsutil cp {} {}'.format(filenames[0], destdir)
      subprocess.check_call(copy_command.split())
      basename = os.path.basename(filenames[0])
      return os.path.join(destdir, basename)
   return None

def crop_image(nc, data, clat, clon):
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
   print(old_grid)

   # now do remapping
   return pr.kd_tree.resample_nearest(old_grid, data, new_grid, radius_of_influence=50000)

def plot_image(ncfilename, outfile, clat, clon):
    import matplotlib
    matplotlib.use('Agg') # headless display
    import numpy as np
    from netCDF4 import Dataset
    import matplotlib.pyplot as plt
    
    with Dataset(ncfilename, 'r') as nc:
        rad = nc.variables['Rad'][:]
        # See http://www.goes-r.gov/products/ATBDs/baseline/Imagery_v2.0_no_color.pdf
        ref = (rad * np.pi * 0.3) / 663.274497
        ref = np.minimum( np.maximum(ref, 0.0), 1.0 )

        print('The image has values between {} and {}'.format(np.min(ref), np.max(ref)))

        # crop to area of interest
        ref = crop_image(nc, ref, clat, clon)
        print('The cropped image has values between {} and {}'.format(np.min(ref), np.max(ref)))

        # plotting to jpg file
        fig = plt.figure()
        plt.imshow(ref, vmin=0.0, vmax=0.2, cmap=plt.cm.hot)
        fig.savefig(outfile)
        plt.close('all')
        return outfile
    return None


if __name__ == '__main__':
    import tempfile
    import shutil,os
    import numpy as np
    from datetime import datetime

    outdir = 'image'
    shutil.rmtree(outdir, ignore_errors=True)
    os.mkdir(outdir)
    tmpdir = tempfile.mkdtemp()
    print('Writing temporary files to {}'.format(tmpdir))

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
       gcs_pattern = 'gs://gcp-public-data-goes-16/ABI-L1b-RadF/{0}/{1:03d}/{2:02d}/*C14*_s{0}{1:03d}{2:02d}*'.format(dt.year, dayno, dt.hour)
       #gcs_pattern = 'gs://gcp-public-data-goes-16/ABI-L1b-RadC/{0}/{1:03d}/{2:02d}/*C14*_s{0}{1:03d}{2:02d}*'.format(dt.year, dayno, dt.hour)
       local_file = copy_fromgcs(gcs_pattern, tmpdir)

       # create image
       jpgfile = '{}/ir_{}{}{}.jpg'.format(outdir, dt.year, dayno, dt.hour)
       jpgfile = plot_image(local_file, jpgfile, lat, lon)

       break

    # cleanup
    shutil.rmtree(tmpdir)
    exit(-1)
