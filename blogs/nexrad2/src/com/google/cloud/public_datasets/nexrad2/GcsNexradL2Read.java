/*
 * Copyright (C) 2017 Google Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not
 * use this file except in compliance with the License. You may obtain a copy of
 * the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations under
 * the License.
 */
package com.google.cloud.public_datasets.nexrad2;

import java.io.File;
import java.io.IOException;
import java.util.Formatter;
import java.util.Locale;

import ucar.nc2.VariableSimpleIF;
import ucar.nc2.constants.FeatureType;
import ucar.nc2.dt.RadialDatasetSweep;
import ucar.nc2.ft.FeatureDatasetFactoryManager;
import ucar.nc2.units.DateUnit;

/**
 * Reads NEXRAD Level 2 public data from GCS and provides access to it via
 * NetCDF API Because GCS stores one hour of data in a single tar, this class
 * provides access to one hour of nexrad data.
 * 
 * @author vlakshmanan
 *
 */
public class GcsNexradL2Read implements AutoCloseable {
  private final GcsUntar untar;
  
  /**
   * For example: gs://gcp-public-data-nexrad-l2/2016/05/03/KAMA/
   * NWS_NEXRAD_NXL2DP_KAMA_20160503000000_20160503005959.tar
   * 
   * @param tarFileName
   */
  public GcsNexradL2Read(String tarFileName) throws IOException {
    this.untar = GcsUntar.fromGcsOrLocal(tarFileName);
  }

  @Override
  public void close() throws Exception {
    untar.close();
  }

  public RadialDatasetSweep[] getVolumeScans() throws IOException {
    // See: http://www.unidata.ucar.edu/software/thredds/current/netcdf-java/tutorial/RadialDatatype.html
    File[] files = untar.getFiles();
    RadialDatasetSweep[] result = new RadialDatasetSweep[files.length];
    Formatter errors = new Formatter(new StringBuilder(), Locale.US);
    for (int i = 0; i < result.length; ++i) {
      result[i] = (RadialDatasetSweep) FeatureDatasetFactoryManager.open(//
          FeatureType.RADIAL, files[i].getAbsolutePath(), null, errors);
    }
    return result;
  }

  public static RadialDatasetSweep.RadialVariable getDataVariable(RadialDatasetSweep volume, String name) {
    for (VariableSimpleIF var : volume.getDataVariables()) {
      if (var.getFullName().equals(name)) {
        return (RadialDatasetSweep.RadialVariable) var;
      }
    }
    
    StringBuilder sb = new StringBuilder();
    for (VariableSimpleIF var : volume.getDataVariables()) {
      sb.append(var.getFullName());
      sb.append(' ');
    }
    throw new RuntimeException("Variable " + name + " not found; choose one of {" + sb + "}");
  }

  public static void main(String[] args) throws Exception {
    String tarFile = "/Users/vlakshmanan/data/nexrad/2016%2F05%2F03%2FKAMA%2FNWS_NEXRAD_NXL2DP_KAMA_20160503090000_20160503095959.tar";
    // String tarFile =
    // "gs://gcp-public-data-nexrad-l2/2016/05/03/KAMA/NWS_NEXRAD_NXL2DP_KAMA_20160503000000_20160503005959.tar";

    System.out.println("Reading " + tarFile);
    try (GcsNexradL2Read hourly = new GcsNexradL2Read(tarFile)) {
      for (RadialDatasetSweep volume : hourly.getVolumeScans()) {
        RadialDatasetSweep.Sweep ref = getDataVariable(volume, "Reflectivity").getSweep(0);
        DateUnit timeUnit = volume.getTimeUnits();
        System.out.println(volume.getRadarID() + " refl " + ref.getMeanElevation() + " at "
            + timeUnit.makeStandardDateString(ref.getTime(0)));
      }
    }
  }
}
