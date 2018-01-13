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

GOES_PUBLIC_BUCKET='gcp-public-data-goes-16'

def list_gcs(bucket, gcs_prefix, gcs_patterns):
   import google.cloud.storage as gcs
   bucket = gcs.Client().get_bucket(bucket)
   blobs = bucket.list_blobs(prefix=gcs_prefix, delimiter='/')
   result = []
   if gcs_patterns == None or len(gcs_patterns) == 0:
      for b in blobs:
          result.append(b)
   else:
      for b in blobs:
          match = True
          for pattern in gcs_patterns:
              if not pattern in b.path:
                 match = False
          if match:
              result.append(b)
   return result

def copy_fromgcs(bucket, objectId, destdir):
   import os.path
   import logging
   import google.cloud.storage as gcs
   bucket = gcs.Client().get_bucket(bucket)
   blob = bucket.blob(objectId)
   basename = os.path.basename(objectId)
   logging.info('Downloading {}'.format(basename))
   dest = os.path.join(destdir, basename)
   blob.download_to_filename(dest)
   return dest

def copy_togcs(localfile, bucket_name, blob_name):
   import logging
   import google.cloud.storage as gcs
   bucket = gcs.Client().get_bucket(bucket_name)
   blob = bucket.blob(blob_name)
   blob.upload_from_filename(localfile)
   logging.info('{} uploaded to gs://{}/{}'.format(localfile,
        bucket_name, blob_name))
   return blob

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

def get_objectId_at(dt, product='ABI-L1b-RadF', channel='C14'):
   import os, logging
   # get first 11-micron band (C14) at this hour
   # See: https://www.goes-r.gov/education/ABI-bands-quick-info.html
   logging.info('Looking for data collected on {}'.format(dt))
   dayno = dt.timetuple().tm_yday
   gcs_prefix = '{}/{}/{:03d}/{:02d}/'.format(product, dt.year, dayno, dt.hour)
   gcs_patterns = [channel,
          's{}{:03d}{:02d}'.format(dt.year, dayno, dt.hour)]
   blobs = list_gcs(GOES_PUBLIC_BUCKET, gcs_prefix, gcs_patterns)
   if len(blobs) > 0:
      objectId = blobs[0].path.replace('%2F','/').replace('/b/{}/o/'.format(GOES_PUBLIC_BUCKET),'')
      logging.info('Found {} for {}'.format(objectId, dt))
      return objectId
   else:
      logging.error('No matching files found for gs://{}/{}* containing {}'.format(GOES_PUBLIC_BUCKET, gcs_prefix, gcs_patterns))
      return None

def parse_timestamp(timestamp):
    from datetime import datetime
    dt = datetime.strptime(timestamp[:19], '%Y-%m-%d %H:%M:%S')
    return dt

def parse_line(line):
    fields = line.split(',')
    return parse_timestamp(fields[6]), float(fields[8]), float(fields[9])

def goes_to_jpeg(objectId, lat, lon, outbucket, outfilename):
    import os, shutil, tempfile, subprocess, logging
    import os.path

    # if get_objectId_at fails, it returns None
    if objectId == None:
        logging.error('Skipping GOES object creation since no GCS file specified')
        return


    tmpdir = tempfile.mkdtemp()
    local_file = copy_fromgcs('gcp-public-data-goes-16', objectId, tmpdir)
    logging.info('Creating image from {} near {},{}'.format(os.path.basename(local_file), lat, lon))

    # create image in temporary dir, then move over
    jpgfile = os.path.join(tmpdir, os.path.basename(outfilename))
    jpgfile = plot_image(local_file, jpgfile, lat, lon)
    logging.info('Created {} from {}'.format(os.path.basename(jpgfile), os.path.basename(local_file)))

    # move over
    if outbucket != None:
        copy_togcs(jpgfile, outbucket, outfilename)
        outfilename = 'gs://{}/{}'.format(outbucket, outfilename)
    else:
        subprocess.check_call(['mv', jpgfile, outfilename])

    # cleanup
    shutil.rmtree(tmpdir)
    logging.info('Created {} from {}'.format(outfilename, os.path.basename(local_file)))

    return outfilename


def only_infrared(message):
  import json, logging
  try:
    # message is a string in json format, so we need to parse it as json
    #logging.debug(message)
    result = json.loads(message)
    # e.g. ABI-L2-CMIPF/2017/306/21/OR_ABI-L2-CMIPF-M4C01_G16_s20173062105222_e20173062110023_c20173062110102.nc
    if 'C14_G16' in result['name']:
        yield result['name'] #filename
  except:
    import sys
    logging.warn(sys.exc_info()[0])
    pass
