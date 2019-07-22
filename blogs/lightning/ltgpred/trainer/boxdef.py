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
import numpy as np

class BoxDef(object):

  def __init__(self, train_patch_radius, label_patch_radius, stride):
    self.train_patch_radius = train_patch_radius
    self.stride = stride
    self.label_patch_radius = label_patch_radius


  def get_prediction_grid_centers(self, ref):
    neighborhood_size = self.train_patch_radius + self.label_patch_radius # slop
    cy, cx = np.meshgrid(
        np.arange(neighborhood_size,
                  ref.shape[0] - neighborhood_size,
                  self.stride),
        np.arange(neighborhood_size,
                  ref.shape[1] - neighborhood_size,
                  self.stride))
    cy = cy.ravel()
    cx = cx.ravel()
    return zip(cy, cx)


  def rawdata_input_fn(self, ref, ltg, griddef, ltgfcst = None):
    """Input function that yields example dicts for each box in grid."""
    for cy, cx in self.get_prediction_grid_centers(ref):
      # restrict to grids where there is currently lightning in the area
      interesting = np.sum(
        ltg[cy - self.train_patch_radius:cy + self.train_patch_radius + 1,
            cx - self.train_patch_radius:cx + self.train_patch_radius + 1]) > 0.5
      if interesting:
        label = (np.sum(
                  ltgfcst[cy - self.label_patch_radius:cy + self.label_patch_radius + 1,
                          cx - self.label_patch_radius:cx + self.label_patch_radius + 1])
                 > 0.5 if ltgfcst is not None else None)
        example = {
            'cy':
                cy,
            'cx':
                cx,
            'lon':
                griddef.lons[cy][cx],
            'lat':
                griddef.lats[cy][cx],
            'ref_center':
                ref[cy][cx],
            'ltg_center':
                ltg[cy][cx],
            'ref_smallbox':
                ref[cy - self.label_patch_radius:cy + self.label_patch_radius + 1,
                    cx - self.label_patch_radius:cx + self.label_patch_radius + 1],
            'ref_bigbox':
                ref[cy - self.train_patch_radius:cy + self.train_patch_radius + 1,
                    cx - self.train_patch_radius:cx + self.train_patch_radius + 1],
            'ltg_smallbox':
                ltg[cy - self.label_patch_radius:cy + self.label_patch_radius + 1,
                    cx - self.label_patch_radius:cx + self.label_patch_radius + 1],
            'ltg_bigbox':
                ltg[cy - self.train_patch_radius:cy + self.train_patch_radius + 1,
                    cx - self.train_patch_radius:cx + self.train_patch_radius + 1],
            'has_ltg':
                label
        }
        yield example
