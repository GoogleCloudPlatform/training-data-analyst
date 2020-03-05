#!/usr/bin/env python3

"""
Copyright Google Inc. 2019
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

# Download a 3600x1800 resolution CSV file from https://neo.sci.gsfc.nasa.gov/view.php?datasetId=SEDAC_POP
# Save it as popdensity.csv and invoke this program specifying --format=nasa
# Else download 30-arcsec resolution ASCII file from https://sedac.ciesin.columbia.edu/data/set/gpw-v4-population-density-rev11/data-download
# Unzip the downloaded file and invoke this program specifying --format=sedac


import argparse
import json
import gzip
import numpy as np

def create_geo(LATRES, LONRES, ORIGIN_LAT, ORIGIN_LON, rowno, startcol, endcol):
  # represent each rectangle by a polygon of its corners
  top = ORIGIN_LAT - rowno * LATRES
  bot = ORIGIN_LAT - (rowno+1) * LATRES
  left = ORIGIN_LON + startcol * LONRES
  right = ORIGIN_LON + endcol * LONRES

  poly = json.dumps({
      'type': 'Polygon',
      'coordinates': [
          [ # polygon 1
            [left, top],  # topleft
            [left, bot],  # botleft
            [right, bot], # botright
            [right, top], # topright
            [left, top]   # same as first point
          ]
      ]
  })

  center = 'POINT({:2f} {:2f})'.format( (left+right)/2, (top+bot)/2 )
  return poly, center, endcol

def create_rectangle_geo(LATRES, LONRES, ORIGIN_LAT, ORIGIN_LON, rowno, startcol, linedata):
  # find a rectangle of pixels with the same value, and represent that pixel instead
  endcol = startcol
  while (endcol < len(linedata)) and (linedata[endcol] == linedata[startcol]):
    endcol = endcol + 1
  return create_geo(LATRES, LONRES, ORIGIN_LAT, ORIGIN_LON, rowno, startcol, endcol)


def get_next_value(ifp):
  return float( ifp.readline().strip().split()[1] )


def ascii_to_geojson(
  format, infiles, outfile
):
   print('Creating {} from {} input {}'.format(outfile, format, infiles))
   with gzip.open(outfile, 'w') as ofp:
     for infile in infiles:
       ifp = open(infile)

       # header
       if format == 'nasa':
         ncols = 3600
         nrows = 1800
         LATRES = LONRES = 0.1
         ORIGIN_LAT = 90
         ORIGIN_LON = -180
         BADVALUE = 99999.0
         YEAR = 2000
       else:
         ncols = get_next_value(ifp)
         nrows = get_next_value(ifp)
         ORIGIN_LON = get_next_value(ifp)
         yllcorner = get_next_value(ifp)
         LATRES = LONRES = get_next_value(ifp)
         BADVALUE = get_next_value(ifp)
         ORIGIN_LAT = yllcorner + nrows * LATRES
         YEAR = 2020  # FIXME: parse filename

       # data
       print('{} from {:.4f},{:.4f} at {}'.format(infile, ORIGIN_LAT, ORIGIN_LON, LATRES), end=' ', flush=True)
       for rowno, line in enumerate(ifp):
         print('.', end='', flush=True)
         if format == 'nasa':
           linedata = [float(x) for x in line.split(',')]
         else:
           linedata = [float(x) for x in line.split()]
         colno = 0
         while colno < len(linedata):
           value = linedata[colno]
           if value != BADVALUE:
             # poly, center, colno = create_geo(LATRES, LONRES, ORIGIN_LAT, ORIGIN_LON, rowno, colno, colno+1)
             poly, center, colno = create_rectangle_geo(LATRES, LONRES, ORIGIN_LAT, ORIGIN_LON, rowno, colno, linedata)
             pixel = {
                'year': YEAR,
                'rowno': rowno,
                'colno': colno,  # one past the last colno of the rectangle, so not intuitive!
                'tile': infile,  # SEDAC split over several tiles
                'location': center,
                'bounds': poly,
                'population_density': value
             }
             outline = json.dumps(pixel) + '\n'
             ofp.write(outline.encode('utf-8'))
           else:
             colno = colno + 1
       print('!')


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Convert downloaded ASCII files to GeoJSON')
  parser.add_argument('--format', help='Specify nasa or sedac')
  parser.add_argument('--input', help='Specify one or more input files', metavar='filename', nargs='+')
  
  args = parser.parse_args()
  ascii_to_geojson(args.format, args.input, 'popdensity_geo.json.gz')
