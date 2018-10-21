#!/usr/bin/env python
"""Create dataset for predicting lightning using Dataflow.

Copyright Google Inc.
2018 Licensed under the Apache License, Version 2.0 (the "License"); you may
not use this file except in compliance with the License. You may obtain a copy
of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required
by applicable law or agreed to in writing, software distributed under the
License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS
OF ANY KIND, either express or implied. See the License for the specific
language governing permissions and limitations under the License.
"""
import argparse
import datetime
import logging
import os
import shutil
import subprocess
import apache_beam as beam
import numpy as np
import tensorflow as tf


class BoxDef(object):

  def __init__(self, predsize, stride):
    self.N = predsize  # pylint: disable=invalid-name
    self.stride = stride
    self.half_size = predsize // 2
    self.N15 = predsize + self.half_size  # pylint: disable=invalid-name


  def get_prediction_grid_centers(self, ref):
    cy, cx = np.meshgrid(
        np.arange(self.N15, ref.shape[0] - self.N15, self.stride),
        np.arange(self.N15, ref.shape[1] - self.N15, self.stride))
    cy = cy.ravel()
    cx = cx.ravel()
    return zip(cy, cx)


  def rawdata_input_fn(self, ref, ltg, griddef, ltgfcst = None):
    """Input function that yields example dicts for each box in grid."""
    for cy, cx in self.get_prediction_grid_centers(ref):
      # restrict to grids where there is currently lightning in the area
      interesting = np.sum(ltg[cy - self.N15:cy + self.N15, cx -
                               self.N15:cx + self.N15]) > 0.5
      if interesting:
        label = (np.sum(ltgfcst[cy - self.half_size:cy + self.half_size, cx -
                                self.half_size:cx + self.half_size]) > 0.5
                 if ltgfcst is not None else None)
        example = {
            'cy':
                cy,
            'cx':
                cx,
            'lon':
                griddef.lons[cy][cx],
            'lat':
                griddef.lats[cy][cx],
            'ref_smallbox':
                ref[cy - self.half_size:cy + self.half_size,
                    cx - self.half_size:cx + self.half_size],
            'ref_bigbox':
                ref[cy - self.N:cy + self.N,
                    cx - self.N:cx + self.N],
            'ltg_smallbox':
                ltg[cy - self.half_size:cy + self.half_size,
                    cx - self.half_size:cx + self.half_size],
            'ltg_bigbox':
                ltg[cy - self.N:cy + self.N,
                    cx - self.N:cx + self.N],
            'has_ltg':
                label
        }
        yield example

