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

import apache_beam as beam
import numpy as np
import argparse, logging
from apache_beam.typehints import with_input_types
from apache_beam.typehints import with_output_types

def find_locations(wire):
   positions = [(0,0)]
   for nav in wire.split(','):
     dir = nav[0]
     if dir == 'R':
       update = (1, 0)
     elif dir == 'U':
       update = (0, 1)
     elif dir == 'L':
       update = (-1, 0)
     else:
       update = (0, -1)
     
     n = int(nav[1:])
     for x in range(n):
       lastpos = positions[-1]
       newpos = (lastpos[0] + update[0],
                 lastpos[1] + update[1])
       positions.append(newpos)
   
   return positions[1:] # remove the 0,0

def find_intersection(kv):
   row, d = kv
   if d['wire1'] and d['wire2']:
      wire1 = d['wire1'][0]
      wire2 = d['wire2'][0]
      for col in wire1:
         if col in wire2:
            yield (row, col)
         
def manhattan(rc):
   row, col = rc
   return abs(row) + abs(col)

if __name__ == '__main__':
   parser = argparse.ArgumentParser(description='Solutions to https://adventofcode.com/2019/ using Apache Beam')
   parser.add_argument('--input', required=True, help='Specify input file')
   parser.add_argument('--output', required=True, help='Specify output file')
   
   options = parser.parse_args()
   runner = 'DirectRunner' # run Beam on local machine, but write outputs to cloud
   logging.basicConfig(level=getattr(logging, 'INFO', None))

   #wires = ('R75,D30,R83,U83,L12,D49,R71,U7,L72', 'U62,R66,U55,R34,D71,R55,D58,R83')
   #wires = ('R98,U47,R26,D63,R33,U87,L62,D20,R33,U53,R51', 'U98,R91,D20,R16,D67,R40,U7,R15,U6,R7')
   wires =  [line.rstrip() for line in open(options.input)]
   print(wires)

   opts = beam.pipeline.PipelineOptions(flags=[])
   p = beam.Pipeline(runner, options=opts)
  
   locations = {'wire1': 
                  (p | 'create1' >> beam.Create(find_locations(wires[0])) 
                     | 'group1'  >> beam.GroupByKey()),
                'wire2':
                  (p | 'create2' >> beam.Create(find_locations(wires[1])) 
                     | 'group2'  >> beam.GroupByKey())
               }

   (locations 
               | 'cogroup'   >> beam.CoGroupByKey()
               | 'intersect' >> beam.FlatMap(find_intersection)
               | 'distance' >> beam.Map(manhattan)
               | 'mindist'  >> beam.CombineGlobally(beam.transforms.combiners.TopCombineFn(1, reverse=True))
               | 'output' >> beam.io.textio.WriteToText(options.output)
   )

   job = p.run()
   if runner == 'DirectRunner':
      job.wait_until_finish()

