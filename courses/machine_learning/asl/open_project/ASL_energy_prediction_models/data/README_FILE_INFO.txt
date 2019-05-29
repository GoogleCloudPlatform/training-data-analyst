Explanation of variables included in the files:


- File points.csv:

	point - Specific id of each meteo point.
	latitude - Latitude coordinate, in decimal degrees. 	
	longitude - Longitude coordinate, in decimal degrees. 


- File historical_meteo.csv:

	point - Specific id of each meteo point.
	available_date - Date and hour that the forecast is made available / performed, in UTC.	
	prediction_date	- Date and hour that corresponds to the forecast, in UTC.
	wind_speed_100m - Wind speed estimated at 100 meters, in m/s.
	wind_direction_100m - Wind direction estimated at 100 meters, in degrees [0-360].	
	temperature - Ambient temperature estimated at groud level, in degrees C.	
	air_density - Air density estimated at ground level, in kg/m3.	
	pressure - Air pressure estimated at ground level, in hPa.	
	precipitation - Rainfall intensity, in mm/m2.
	wind_gust  - Wind gust speed estimated at 10 meters, in m/s.
	radiation - Solar radiation estimated at ground level, in W/m2.	
	wind_speed - Wind speed estimated at 10 meters, in m/s.	
	wind_direction - Wind direction estimated at 10 meters, in degrees [0-360].

- Daily forecast files in format |yyyy-mm-dd_hh:mm:ss|.csv:
	
	point - Specific id of each meteo point.
	available_date - Date and hour that the forecast is made available / performed, in UTC.	
	prediction_date	- Date and hour that corresponds to the forecast, in UTC.
	wind_speed_100m - Wind speed estimated at 100 meters, in m/s.
	wind_direction_100m - Wind direction estimated at 100 meters, in degrees [0-360].	
	temperature - Ambient temperature estimated at groud level, in degrees C.	
	air_density - Air density estimated at ground level, in kg/m3.	
	pressure - Air pressure estimated at ground level, in hPa.	
	precipitation - Rainfall intensity, in mm/m2.
	wind_gust  - Wind gust speed estimated at 10 meters, in m/s.
	radiation - Solar radiation estimated at ground level, in W/m2.	
	wind_speed - Wind speed estimated at 10 meters, in m/s.	
	wind_direction - Wind direction estimated at 10 meters, in degrees [0-360].