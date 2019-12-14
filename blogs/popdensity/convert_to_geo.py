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
# Save it as popdensity.csv

import json
import gzip

LATRES = LONRES = 0.1
ORIGIN_LAT = 90
ORIGIN_LON = -180

with gzip.open('popdensity_geo.json.gz', 'w') as ofp:
 for rowno, line in enumerate(open('popdensity.csv')):
   print('.', end='', flush=True)
   linedata = [float(x) for x in line.split(',')]
   for colno, value in enumerate(linedata):
     if value != 99999.0:
       # represent each pixel by a polygon of its corners
       top = ORIGIN_LAT - rowno * LATRES
       bot = ORIGIN_LAT - (rowno+1) * LATRES
       left = ORIGIN_LON + colno * LONRES
       right = ORIGIN_LON + (colno+1) * LONRES
       poly = 'POLYGON(({:.2f} {:.2f}, {:.2f} {:.2f}, {:.2f} {:.2f}, {:.2f} {:.2f}, {:.2f} {:.2f}))'.format(
                 left, top,  # topleft
                 left, bot,  # botleft
                 right, bot, # botright
                 right, top, # topright
                 left, top   # same as first point
              )
       center = 'POINT({:2f} {:2f})'.format( (left+right)/2, (top+bot)/2 )
       pixel = {
          'rowno': rowno,
          'colno': colno,
          'location': center,
          'bounds': poly,
          'population_density': value
       }
       
       outline = json.dumps(pixel) + '\n'
       ofp.write(outline.encode('utf-8'))
   
