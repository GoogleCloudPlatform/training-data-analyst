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
public class Airport implements Serializable {
	String name;
	double latitude;
	double longitude;

	public Airport(String[] fields, FieldNumberLookup e) {
		this.name = fields[e.FN_airport];
		this.latitude = Double.parseDouble(fields[e.FN_lat]);
		this.longitude = Double.parseDouble(fields[e.FN_lon]);
	}

	public Airport() {
		// for serialization only
	}
}