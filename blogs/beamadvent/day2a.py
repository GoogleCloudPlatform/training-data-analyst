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

def handle_ints(ints, startpos=0):
   if ints[startpos] == 99:
      return ints
   x1 = ints[startpos+1]
   x2 = ints[startpos+2]
   outpos = ints[startpos+3]
   if ints[startpos] == 1:
      ints[outpos] = ints[x1] + ints[x2]
   elif ints[startpos] == 2:
      ints[outpos] = ints[x1] * ints[x2]
   return handle_ints(ints, startpos+4)

def handle_intcode(intcode):
   input = [int(x) for x in intcode.split(',')]
   output = handle_ints(input)
   return ','.join([str(x) for x in output])

def run_1202(intcode):
   input = [int(x) for x in intcode.split(',')]
   input[1] = 12
   input[2] = 2
   output = handle_ints(input)
   return output[0]

def try_working():
   assert handle_intcode('1,0,0,0,99') == '2,0,0,0,99'
   assert handle_intcode('2,3,0,3,99') == '2,3,0,6,99'
   assert handle_intcode('2,4,4,5,99,0') == '2,4,4,5,99,9801'
   assert handle_intcode('1,1,1,4,99,5,6,0,99') == '30,1,1,4,2,5,6,0,99'
   print('Assertions passed')

if __name__ == '__main__':
   parser = argparse.ArgumentParser(description='Solutions to https://adventofcode.com/2019/ using Apache Beam')
   parser.add_argument('--input', required=True, help='Specify input file')
   parser.add_argument('--output', required=True, help='Specify output file')
   
   options = parser.parse_args()
   runner = 'DirectRunner' # run Beam on local machine, but write outputs to cloud
   logging.basicConfig(level=getattr(logging, 'INFO', None))

   opts = beam.pipeline.PipelineOptions(flags=[])
   p = beam.Pipeline(runner, options=opts)
   (p
        | 'read' >> beam.io.textio.ReadFromText(options.input)
        | 'run_1202' >> beam.Map(run_1202)
        | 'output' >> beam.io.textio.WriteToText(options.output)
   )
   job = p.run()
   if runner == 'DirectRunner':
      job.wait_until_finish()

