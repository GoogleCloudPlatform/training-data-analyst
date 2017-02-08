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

package com.google.cloud.training.flights;

import java.io.Serializable;

import org.apache.beam.sdk.coders.AvroCoder;
import org.apache.beam.sdk.coders.DefaultCoder;



@SuppressWarnings("serial")
@DefaultCoder(AvroCoder.class)
public class AirportStats implements Serializable {
	Airport airport;
	double arr_delay, dep_delay;
	String timestamp;
	int num_flights;
	
	public AirportStats(Airport airport, double arr_delay, double dep_delay, String timestamp, int num_flights) {
		this.airport = airport;
		this.arr_delay = arr_delay;
		this.dep_delay = dep_delay;
		this.timestamp = timestamp;
		this.num_flights = num_flights;
	}

	public AirportStats() {
		// for serialization only
	}
}
