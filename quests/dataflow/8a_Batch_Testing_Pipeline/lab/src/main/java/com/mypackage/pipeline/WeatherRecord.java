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
import java.util.Objects;

/**
 * A class used for parsing CSV weather records
 * Annotated with @DefaultSchema to the allow the use of Beam Schemas and <Row> object
 */
@DefaultSchema(JavaFieldSchema.class)
public class WeatherRecord {
    String locId;
    Double lat;
    Double lng;
    String date;
    Double lowTemp;
    Double highTemp;
    Double precip;
        
    @SchemaCreate
    WeatherRecord(String locId, Double lat, Double lng, String date, Double lowTemp, Double highTemp, Double precip){
        this.locId = locId;
        this.lat = lat;
        this.lng = lng;
        this.date = date;
        this.lowTemp = lowTemp;
        this.highTemp = highTemp;
        this.precip = precip;
        }

    /**
     * Custom equals and hashCode method to check for equality
     */
    
    @Override
    public int hashCode(){
        return Objects.hash(locId, lat, lng, date, lowTemp, highTemp, precip);
    }

    @Override
    public boolean equals(final Object obj){
        if(obj instanceof WeatherRecord){
            final WeatherRecord other = (WeatherRecord) obj;
            return (locId.equals(other.locId))
                && (Double.compare(lat, other.lat) == 0)
                && (Double.compare(lng, other.lng) == 0)
                && (date.equals(other.date))
                && (Double.compare(lowTemp, other.lowTemp) == 0)
                && (Double.compare(highTemp, other.highTemp) == 0)
                && (Double.compare(precip, other.precip) == 0);
        } else{
            return false;
        }
    }
        
}