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

@SuppressWarnings("serial")
public class FieldNumberLookup implements Serializable {
	String eventName;
	int FN_airport, FN_lat, FN_lon, FN_delay, FN_timestamp; // field numbers

	public static FieldNumberLookup create(String event) {
		if (event.equals("arrived")) {
			// from table in Ch 2
			return new FieldNumberLookup(event, 13, 31, 32, 23, 22);
		} else {
			return new FieldNumberLookup(event, 9, 28, 29, 16, 15);
		}
	}
	
	private FieldNumberLookup(String e, int fN_airport, int fN_lat, int fN_lon, int fN_delay, int fN_timestamp) {
		eventName = e;
		FN_airport = fN_airport - 1; // zero-based
		FN_lat = fN_lat - 1;
		FN_lon = fN_lon - 1;
		FN_delay = fN_delay - 1;
		FN_timestamp = fN_timestamp - 1;
	}
	
	public FieldNumberLookup() {
		// for serialization
	}
}