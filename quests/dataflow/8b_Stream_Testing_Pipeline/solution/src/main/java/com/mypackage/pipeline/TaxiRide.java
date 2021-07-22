/*
 * Copyright (C) 2021 Google Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.mypackage.pipeline;

import org.apache.beam.sdk.schemas.JavaFieldSchema;
import org.apache.beam.sdk.schemas.annotations.DefaultSchema;
import org.apache.beam.sdk.schemas.annotations.SchemaCreate;

/**
 * A class used for parsing JSON web server events
 * Annotated with @DefaultSchema to the allow the use of Beam Schema and <Row> object
 */
@DefaultSchema(JavaFieldSchema.class)
public class TaxiRide {
    String ride_id;
    Integer point_idx;
    Double latitude;
    Double longitude;
    String timestamp;
    Double meter_reading;
    Double meter_increment;
    String ride_status;
    Long passenger_count;

    @SchemaCreate
    TaxiRide(String ride_id, Integer point_idx, Double latitude, Double longitude, String timestamp,
        Double meter_reading, Double meter_increment, String ride_status,  Long passenger_count){
            this.ride_id = ride_id;
            this.point_idx = point_idx;
            this.latitude = latitude;
            this.longitude = longitude;
            this.timestamp = timestamp;
            this.meter_reading = meter_reading;
            this.meter_increment = meter_increment;
            this.ride_status = ride_status;
            this.passenger_count = passenger_count;

    }
}

