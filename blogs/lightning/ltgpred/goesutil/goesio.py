#!/usr/bin/env python
"""Copyright Google Inc.

2018 Licensed under the Apache License, Version 2.0 (the "License"); you may
not use this file except in compliance with the License. You may obtain a copy
of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required
by applicable law or agreed to in writing, software distributed under the
License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS
OF ANY KIND, either express or implied. See the License for the specific
language governing permissions and limitations under the License.
"""

from __future__ import division
from __future__ import print_function
from datetime import datetime
from datetime import timedelta
import logging
import os
import os.path
import shutil
import tempfile
import threading
from netCDF4 import Dataset
import numpy as np
import pyresample as pr
from retrying import retry
import google.cloud.storage as gcs

GOES_PUBLIC_BUCKET = 'gcp-public-data-goes-16'
RETRY_MIN_MSECS = 100
RETRY_MAX_MSECS = 10000

_gcs_client = None
_gcs_client_lock = threading.Lock()


def cached_gcs_client():
  global _gcs_client
  with _gcs_client_lock:
    if not _gcs_client:
      _gcs_client = gcs.Client()
    return _gcs_client
  return _gcs_client


def reset_gcs_client_and_retry(exception):  # pylint: disable=unused-argument
  global _gcs_client
  with _gcs_client_lock:
    _gcs_client = None  # force recreate
  _gcs_client = cached_gcs_client()
  return True  # reset and retry whenever any exception is thrown


def parse_blobpath(blob_path):
  blob_path = blob_path.replace('%2F', '/')
  blob_path = blob_path[3:]  # /b/
  slash_loc = blob_path.index('/')
  bucket_name = blob_path[:slash_loc]
  blob_name = blob_path[(slash_loc + 3):]  # /o/
  return bucket_name, blob_name


@retry(
    wait_exponential_multiplier=RETRY_MIN_MSECS,
    wait_exponential_max=RETRY_MAX_MSECS,
    retry_on_exception=reset_gcs_client_and_retry)
def list_gcs_paths(bucket, gcs_prefix, gcs_patterns=None):
  """list GCS blobs in a bucket starting with the gcs_prefix.

  Args:
    bucket (google.cloud.storage.Bucket): bucket
    gcs_prefix (string): prefix
    gcs_patterns (list of str): return only blobs whose name contains all these
      strings.

  Returns:
    list of blob URLs
  """
  bucket = cached_gcs_client().get_bucket(bucket)
  blobs = bucket.list_blobs(prefix=gcs_prefix, delimiter='/')
  result = []
  if gcs_patterns:
    for b in blobs:
      match = True
      for pattern in gcs_patterns:
        if pattern not in b.path:
          match = False
      if match:
        result.append(b.path)
  else:
    for b in blobs:
      result.append(b.path)
  return result


@retry(
    wait_exponential_multiplier=RETRY_MIN_MSECS,
    wait_exponential_max=RETRY_MAX_MSECS,
    retry_on_exception=reset_gcs_client_and_retry)
def copy_fromgcs(blob_path, destdir):
  """download GCS blobs to a local directory.

  Args:
    blob_path (string): source file, Blob.path URL
    destdir (string): local directory, has to exist

  Returns:
    destination filename
  """
  bucket, object_id = parse_blobpath(blob_path)
  bucket = cached_gcs_client().get_bucket(bucket)
  blob = bucket.blob(object_id)
  basename = os.path.basename(object_id)
  logging.info('Downloading %s', basename)
  dest = os.path.join(destdir, basename)
  blob.download_to_filename(dest)
  return dest


@retry(
    wait_exponential_multiplier=RETRY_MIN_MSECS,
    wait_exponential_max=RETRY_MAX_MSECS,
    retry_on_exception=reset_gcs_client_and_retry)
def copy_togcs(localfile, bucket_name, blob_name):
  bucket = cached_gcs_client().get_bucket(bucket_name)
  blob = bucket.blob(blob_name)
  blob.upload_from_filename(localfile)
  logging.info('%s uploaded to gs://%s/%s', localfile, bucket_name, blob_name)
  return blob


def create_conus_griddef(latlonres):
  # CONUS
  minlon, minlat, maxlon, maxlat = -125, 24, -66, 50

  # output grid in equal-lat-lon
  lats = np.arange(minlat, maxlat, latlonres)
  lons = np.arange(minlon, maxlon, latlonres)
  lons, lats = np.meshgrid(lons, lats)
  return pr.geometry.GridDefinition(lons=lons, lats=lats)


def create_data_grid(nc, data, griddef):
  """Create a ndarray of the data in the netcdf file.

  Args:
    nc (NetcdfFile): file
    data (str): which variable to pull out
    griddef (pyresample.GridDefinition): output grid definition

  Returns:
    ndarray of data in specified grid
  """
  # Subsatellite_Longitude is where the GEO satellite is
  lon_0 = nc.variables['nominal_satellite_subpoint_lon'][0]
  ht_0 = nc.variables['nominal_satellite_height'][0] * 1000  # meters
  x = nc.variables['x'][:] * ht_0  # / 1000.0
  y = nc.variables['y'][:] * ht_0  # / 1000.0
  nx = len(x)
  ny = len(y)
  max_x, min_x, max_y, min_y = x.max(), x.min(), y.max(), y.min()
  half_x = (max_x - min_x) / nx / 2.
  half_y = (max_y - min_y) / ny / 2.
  extents = (min_x - half_x, min_y - half_y, max_x + half_x, max_y + half_y)
  old_grid = pr.geometry.AreaDefinition(
      'geos', 'goes_conus', 'geos', {
          'proj': 'geos',
          'h': str(ht_0),
          'lon_0': str(lon_0),
          'a': '6378169.0',
          'b': '6356584.0'
      }, nx, ny, extents)

  # now do remapping
  logging.info('Remapping from %s', old_grid)
  return pr.kd_tree.resample_nearest(
      old_grid, data, griddef, radius_of_influence=50000)


def parse_cmdline_timestamp(timestamp):
  dt = datetime.strptime(timestamp[:19], '%Y-%m-%d %H:%M:%S')
  return dt


def get_timestamp_from_filename(filename):
  pieces = filename.split('_')
  for p in pieces:
    if len(p) > 13 and p[0:2] == 's2':
      return datetime.strptime(p[1:14], '%Y%j%H%M%S')


def get_ir_blob_paths(year, day, hour, channel='C14'):
  ir_blob_paths = list_gcs_paths(
      GOES_PUBLIC_BUCKET, 'ABI-L1b-RadC/{}/{:03d}/{:02d}/'.format(
          year, day, hour), channel)
  return ir_blob_paths


def read_ir_data(blob_path, griddef):
  """Read satellite infrared data from Blob and fit into grid.

  Args:
    blob_path (Blob URL): netcdf file
    griddef (pyresample.GridDefinition): output grid definition

  Returns:
    ndarray of data in specified grid
  """
  tmpdir = tempfile.mkdtemp()
  try:
    ir_file = copy_fromgcs(blob_path, tmpdir)
    with Dataset(ir_file, 'r') as irnc:
      rad = irnc.variables['Rad'][:]
      ref = (rad * np.pi * 0.3) / 663.274497
      ref = np.sqrt(np.minimum(np.maximum(ref, 0.0), 1.0))
      return create_data_grid(irnc, ref, griddef)
  finally:
    try:
      shutil.rmtree(tmpdir)
    except IOError:
      pass


def get_ltg_blob_paths(dt, timespan_minutes):
  """Get lightning GCS blobs as of the datetime, going back N minutes.

  Args:
    dt (datetime): end timestamp
    timespan_minutes (float): how far back?

  Returns:
    list of GCS Blob URLs
  """
  # get all files in the hours included
  startdt = dt - timedelta(minutes=timespan_minutes)
  ltg_blobs = list_gcs_paths(
      GOES_PUBLIC_BUCKET, 'GLM-L2-LCFA/{}/{:03d}/{:02d}/'.format(
          dt.year,
          dt.timetuple().tm_yday, dt.hour), None)
  if startdt.hour != dt.hour:
    assert timespan_minutes < 120, ('this code will work only for 1-2 hours of '
                                    'data')
    year, day, hour = startdt.year, startdt.timetuple().tm_yday, startdt.hour
    ltg_blobs.extend(
        list_gcs_paths(GOES_PUBLIC_BUCKET,
                       'GLM-L2-LCFA/{}/{:03d}/{:02d}/'.format(year, day,
                                                              hour), None))

  # filter to be within the time
  result = []
  for blob_path in ltg_blobs:
    ts = get_timestamp_from_filename(blob_path)
    if startdt <= ts < dt:
      result.append(blob_path)
  return result


def read_ltg_data(blob_path):
  """Read lightning event data from GCS Blob.

  Args:
    blob_path (Blob URL): netcdf file

  Returns:
    tuple of latitude and longitude arrays
  """
  tmpdir = tempfile.mkdtemp()
  try:
    filename = copy_fromgcs(blob_path, tmpdir)
    with Dataset(filename, 'r') as nc:
      event_lat = nc.variables['event_lat'][:]
      event_lon = nc.variables['event_lon'][:]
      print('{} events'.format(len(event_lat)), end='; ')
      return event_lat, event_lon
  finally:
    try:
      shutil.rmtree(tmpdir)
    except IOError:
      pass


def create_ltg_grid(ltg_blob_paths, griddef, event_influence_km):
  """Read lightning event data from Blobs and fit into grid.

  Args:
    ltg_blob_paths (list of Blob URLs): list of netcdf file
    griddef (pyresample.GridDefinition): output grid definition
    event_influence_km (float): How far does a lightning flash influence?

  Returns:
    ndarray of data in specified grid
  """
  # create swath with lightning points
  ltg_lats, ltg_lons, data = np.array([0]), np.array([0]), np.array([0])
  for blob_path in ltg_blob_paths:
    event_lat, event_lon = read_ltg_data(blob_path)
    ltg_lats = np.append(ltg_lats, event_lat)
    ltg_lons = np.append(ltg_lons, event_lon)
    data = np.append(data, np.ones_like(event_lat))
  swath_def = pr.geometry.SwathDefinition(lats=ltg_lats, lons=ltg_lons)

  # resample these points to a grid
  result = pr.kd_tree.resample_nearest(
      swath_def,
      data,
      griddef,
      radius_of_influence=1000 * event_influence_km,
      epsilon=0.5,
      fill_value=0)

  return result


if __name__ == '__main__':
  conus = create_conus_griddef(0.02)
  irblob_path = get_ir_blob_paths(2018, 134, 20)[0]  # top of the hour
  print(irblob_path)
  # ref = read_ir_data(irblob, conus)
  # print(ref)

  irdt = get_timestamp_from_filename(irblob_path)
  ltg = create_ltg_grid(get_ltg_blob_paths(irdt, timespan_minutes=5), conus, 3)
  print(ltg)
