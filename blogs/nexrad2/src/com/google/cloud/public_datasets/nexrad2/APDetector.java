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

import java.io.IOException;
import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.TimeZone;

import org.apache.beam.sdk.coders.AvroCoder;
import org.apache.beam.sdk.coders.DefaultCoder;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import ucar.nc2.dt.RadialDatasetSweep;
import ucar.nc2.dt.RadialDatasetSweep.Sweep;

/**
 * Applies a simple rule to identify potential AP cases.
 * 
 * @author vlakshmanan
 *
 */
public class APDetector {
  private static final Logger log = LoggerFactory.getLogger(APDetector.class);

  @DefaultCoder(AvroCoder.class)
  static class AnomalousPropagation {
    public String radarId;
    public Date time;
    public float azimuth, range;
    public AnomalousPropagation(String radarId, Date time, float azimuth, float range) {
      this.radarId = radarId;
      this.time = time;
      this.azimuth = azimuth;
      this.range = range;
    }
   
    public String toCsv() {
      DateFormat df = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss");
      df.setTimeZone(TimeZone.getTimeZone("UTC"));
      return radarId + "," + df.format(time) + "," + azimuth + "," + range;
    }
    public AnomalousPropagation(){
    }
  }
  
  public static List<AnomalousPropagation> findAP(RadialDatasetSweep volume) {
    List<AnomalousPropagation> result = new ArrayList<>();
    // find locations with zero velocity, refl at lowest sweep > 35 dBZ
    // and difference between two lowest sweeps > 20 dBZ
    try {
      final String radarId = volume.getRadarID();
      
      RadialDatasetSweep.RadialVariable vel = GcsNexradL2Read.getDataVariable(volume, "RadialVelocity");
      RadialDatasetSweep.RadialVariable ref = GcsNexradL2Read.getDataVariable(volume, "Reflectivity");
    
      // align all the data to lowest reflectivity scan
      RadialDatasetSweep.Sweep ref_lowest = ref.getSweep(0);    
      float[][] vel_lowest = getAlignedData(vel.getSweep(0), ref_lowest);
      float[][] ref_second = getAlignedData(ref.getSweep(1), ref_lowest);
      final Date ref_time = ref_lowest.getStartingTime();
      for (int radial=0; radial < ref_lowest.getRadialNumber(); ++radial) {
        float[] ref_lowest_data = ref_lowest.readData(radial);
        for (int gate=0; gate < ref_lowest.getGateNumber(); ++gate) {
          if (ref_lowest_data[gate] > 35 && //
              vel_lowest[radial][gate] > -0.5 && //
              vel_lowest[radial][gate] < 0.5 && //
              (ref_lowest_data[gate] - ref_second[radial][gate]) > 20
              ) {
            // conditions met
            float az = ref_lowest.getAzimuth(radial);
            float rn = ref_lowest.getRangeToFirstGate() + ref_lowest.getGateSize() * (gate + 0.5f);
            AnomalousPropagation ap = new AnomalousPropagation(radarId, ref_time, az, rn);
            result.add(ap);
          }
        }
      }
      
    } catch (Exception e) {
      log.error("Failed for " + volume.getRadarID() + " at " + volume.getTimeUnits(), e);
    }
    return result;
  }

  private static float[][] getAlignedData(Sweep fromData, Sweep toGeometry) throws IOException {
    float az_tol = (float) (toGeometry.getBeamWidth() * 0.5);
    float[][] result = new float[toGeometry.getRadialNumber()][toGeometry.getGateNumber()];
    for (int toRadial=0; toRadial < result.length; ++toRadial) {
      int fromRadial = findClosestRadial(fromData, toGeometry.getAzimuth(toRadial), az_tol);
      if (fromRadial >= 0) {
        float[] fromValues = fromData.readData(fromRadial);
        for (int toGate=0; toGate < result[0].length; ++toGate) {
          float to_km = toGeometry.getRangeToFirstGate() + (toGate+0.5f) * toGeometry.getGateSize();
          int fromGate = Math.round((to_km - fromData.getRangeToFirstGate()) / fromData.getGateSize());
          if (fromGate >= 0 && fromGate < fromData.getGateNumber()) {
            result[toRadial][toGate] = fromValues[fromGate];
          } else {
            result[toRadial][toGate] = Float.NaN;
          }
        }
      } else {
        for (int gate=0; gate < result[0].length; ++gate) {
          result[toRadial][gate] = Float.NaN;
        }
      }
    }
    return result;
  }

  private static int findClosestRadial(Sweep data, float azimuth, float tol) throws IOException {
    // a bit inefficient; could be sped up with lookups
    int closest = -1;
    float mindiff = tol;
    for (int i=0; i < data.getRadialNumber(); ++i) {
      float diff = Math.abs(data.getAzimuth(i) - azimuth);
      if (diff > 180) {
        diff = Math.abs(360 - diff);
      }
      if (diff <= mindiff) {
        mindiff = diff;
        closest = i;
      }
    }
    return closest;
  }
  
  public static void main(String[] args) throws Exception {
    //String tarFile = "/Users/vlakshmanan/data/nexrad/2016%2F05%2F03%2FKAMA%2FNWS_NEXRAD_NXL2DP_KAMA_20160503090000_20160503095959.tar";
    String tarFile = "gs://gcp-public-data-nexrad-l2/2012/07/23/KYUX/NWS_NEXRAD_NXL2DP_KYUX_20120723150000_20120723155959.tar";
    
    System.out.println("Reading " + tarFile);
    try (GcsNexradL2Read hourly = new GcsNexradL2Read(tarFile)) {
      for (RadialDatasetSweep volume : hourly.getVolumeScans()) {
        List<AnomalousPropagation> apDetections = APDetector.findAP(volume);
        System.out.println(apDetections.size() + " AP found");
        for (AnomalousPropagation rangeGate : apDetections) {
          System.out.println(rangeGate.toCsv());
        }
      }
    }
  }
}
