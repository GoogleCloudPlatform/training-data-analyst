#!/usr/bin/env python

def copy_fromgcs(gcs_pattern, tmpdir):
   from os import listdir
   from os.path import isfile, join
   shutil.rmtree(tmpdir, ignore_errors=True)
   os.makedirs(tmpdir)
   copy_command = 'gsutil cp {} {}'.format(gcs_pattern, tmpdir)
   subprocess.check_call(copy_command.split())
   onlyfiles = [f for f in listdir(tmpdir) if isfile(join(tmpdir, f))]
   return join(tmpdir, onlyfiles[0])

def crop_image(nc, data, clat, clon):
   import pyresample as pr
   from pyproj import Proj
   import numpy as np
   from pyresample import geometry

   # output grid centered on clat, clon in equal-lat-lon 
   lats = np.arange(clat-1,clat+1,0.01) # approx 1km resolution, 200km extent
   lons = np.arange(clon-1,clon+1,0.01) # approx 1km resolution, 200km extent
   lons, lats = np.meshgrid(lons, lats)
   new_grid = geometry.GridDefinition(lons=lons, lats=lats)

   # Subsatellite_Longitude is where the GEO satellite is 
   lon_0 = nc.variables['nominal_satellite_subpoint_lon'][0]
   ht_0 = nc.variables['nominal_satellite_height'][0] * 1000 # meters
   x = nc.variables['x'][:]
   y = nc.variables['y'][:]
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
   return pr.kd_tree.resample_nearest(old_grid, data, new_grid, radius_of_influence=50000)

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

        # crop to area of interest
        ref = crop_image(nc, ref, clat, clon)

        # plotting
        fig = plt.figure()
        plt.imshow(ref, vmin=0.0, vmax=1.0, cmap='Greys_r')
        fig.savefig(outfile)
        plt.close('all')
        return outfile
    return None


if __name__ == '__main__':
    from datetime import datetime
    import numpy as np
    import subprocess
    import shutil,os

    outdir = 'image'
    shutil.rmtree(outdir, ignore_errors=True)
    os.mkdir(outdir)

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
