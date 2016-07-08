/*
 * Copyright (C) 2016 Google Inc.
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

package com.google.cloud.training.dataanalyst.flights;

import com.google.cloud.dataflow.sdk.coders.AvroCoder;
import com.google.cloud.dataflow.sdk.coders.DefaultCoder;

/**
 * @author vlakshmanan
 *
 */
@DefaultCoder(AvroCoder.class)
public class Flight {
	String date;
	String fromAirport;
	String toAirport;
	int depHour;
	int arrHour;
	double departureDelay;
	double taxiOutTime;
	double distance;
	double arrivalDelay;
	double averageDepartureDelay;
	double averageArrivalDelay;
	String line;

	public double[] getInputFeatures() {
		return new double[] { departureDelay, taxiOutTime, distance, averageDepartureDelay, averageArrivalDelay };
	}

	public String toTrainingCsv() {
		double[] features = this.getInputFeatures();
		boolean ontime = this.arrivalDelay < 15;
		StringBuilder sb = new StringBuilder();
		sb.append(ontime ? 1.0 : 0.0);
		sb.append(",");
		for (int i = 0; i < features.length; ++i) {
			sb.append(features[i]);
			sb.append(",");
		}
		sb.deleteCharAt(sb.length() - 1); // last comma
		return sb.toString();
	}
	
	public Flight newCopy() {
        Flight f = new Flight();
        f.date = this.date;
        f.fromAirport = this.fromAirport;
        f.toAirport = this.toAirport;
        f.depHour = this.depHour;
        f.arrHour = this.arrHour;
        f.departureDelay = this.departureDelay;
        f.taxiOutTime = this.taxiOutTime;
        f.distance = this.distance;
        f.arrivalDelay = this.arrivalDelay;
        f.averageDepartureDelay = this.averageDepartureDelay;
        f.averageArrivalDelay = this.averageArrivalDelay;
        f.line = this.line;
        return f;
	}
}
