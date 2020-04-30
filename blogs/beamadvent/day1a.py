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

def compute_fuel(mass):
   return np.floor(mass/3) - 2

if __name__ == '__main__':
   for input, output in [(12,2), (14,2), (1969,654), (100756,33583)]:
      assert compute_fuel(input) == output
   print('Assertions passed')

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
        | 'tofloat' >> beam.Map(lambda s: float(s))
        | 'fuel' >> beam.Map(compute_fuel)
        | 'total' >> beam.CombineGlobally(sum)
        | 'output' >> beam.io.textio.WriteToText(options.output)
   )
   job = p.run()
   if runner == 'DirectRunner':
      job.wait_until_finish()

