Accompanies the blog post  "Querying geographic raster data in BigQuery the brute force way"

https://medium.com/@lakshmanok/querying-geographic-raster-data-in-bigquery-the-brute-force-way-1da46799d65f
(this post stores it pixel-by-pixel: use convert_to_geo.py to replicate)

and

https://medium.com/google-cloud/how-to-query-geographic-raster-data-in-bigquery-efficiently-b178b1a5e723
(this post stores it as rectangles, and is much more efficient; use convert_to_rect.py to replicate)


Decide whether you want to load the NASA data or the SEDAC data.
The NASA file is smaller (10km resolution) and is what I recommend if you just want to try things out. The SEDAC file is 1km resolution and much more accurate, so do that if you want to use this to make real decisions.
Both datasets are global.

## Option 1: NASA (low resolution)

1. Download a 3600x1800 resolution CSV file from https://neo.sci.gsfc.nasa.gov/view.php?datasetId=SEDAC_POP
2. Assuming you saved it as popdensity.csv, run:
    ```
      ./convert_to_rect.py --format=nasa --input popdensity.csv
    ```
3. Run the following script specifying a tablename in BigQuery (the dataset is hardcoded to advdata) and a staging bucket in GCS:
     ```
      ./load_geo_into_bq.sh  popdensity_nasa   staging-bucket
    ```

4. Try this query in BigQuery to find the most populated urban areas in Washington state:
    ```
    WITH urban_populations AS (
        SELECT 
           lsad_name
           , SUM(ST_AREA(ST_INTERSECTION(bounds, urban_area_geom))/1000000) AS area_sqkm
           , COUNT(1) AS num_rectangles
           , AVG(population_density) AS pop_density
        FROM advdata.popdensity_nasa, `bigquery-public-data.geo_us_boundaries.urban_areas`
        WHERE ST_INTERSECTS(bounds, urban_area_geom) 
              AND STRPOS(lsad_name, ', WA') > 0
        GROUP BY lsad_name
    )
    SELECT 
           *, (area_sqkm * pop_density / 1000000) AS population_millions
    FROM urban_populations
    ORDER BY area_sqkm DESC
    LIMIT 10
    ```

## Option 2: SEDAC (high resolution)

1. Download 30-arcsec resolution ASCII file from https://sedac.ciesin.columbia.edu/data/set/gpw-v4-population-density-rev11/data-download
2. Unzip the downloaded file. You will have 8 tiles with the extension .asc.
3. To load in the global data, run (rect is preferred):
    ```
       ./convert_to_[geo/rect].py --format=sedac --input gpw_*.asc
    ```
    If you want data for just Australia, you could load up only the tile that contains Australia:
    ```
       ./convert_to_rect.py --format=sedac --input gpw_*_8.asc
    ```
    If you want data for just the United States, you need only tiles 1 and 2, so you could do:
    ```
       ./convert_to_rect.py --format=sedac --input gpw_*_1.asc gpw_*_2.asc
    ```   
 4. Run the following script specifying a tablename in BigQuery (the dataset is hardcoded to advdata) and a staging bucket in GCS:
     ```
      ./load_geo_into_bq.sh  popdensity_sedac_[pixels/rectangles]   staging-bucket
    ```  
    Name the table popdensity_sedac_pixels if you ran convert_to_geo.py and popdensity_sedac_rectangles if you ran convert_to_rect.py

 5. If you already have popdensity_sedac_rectangles, skip this step. If you ran convert_to_geo, then you got popdensity_sedac_pixels and you should run the following query in BigQuery to create rectangles (i.e. run-length encode the pixels within a tile that have the same population density):
     ```
     CREATE OR REPLACE TABLE advdata.popdensity_sedac_rectangles AS
     PARTITION BY RANGE_BUCKET(year, GENERATE_ARRAY(2000, 2100, 5))
     CLUSTER BY tile
     OPTIONS(require_partition_filter=True)

     with dissolved AS (
            SELECT 
              year, tile, rowno, population_density,
              ST_UNION( ARRAY_AGG(bounds) ) AS bounds,
            FROM advdata.sedac_pixels
            GROUP BY year, tile, rowno, population_density
     )

     SELECT *, ST_CENTROID(bounds) AS location
     FROM dissolved
     ```
     It will take around 20 minutes.
 6. Try this query in BigQuery to find the most populated urban areas in Washington state:
    ```
    WITH urban_populations AS (
        SELECT 
           lsad_name
           , SUM(ST_AREA(ST_INTERSECTION(bounds, urban_area_geom))/1000000) AS area_sqkm
           , COUNT(1) AS num_rectangles
           , AVG(population_density) AS pop_density
        FROM advdata.popdensity_sedac_rectangles, `bigquery-public-data.geo_us_boundaries.urban_areas`
        WHERE tile = 'gpw_v4_population_density_rev11_2020_30_sec_1.asc'
              AND ST_INTERSECTS(bounds, urban_area_geom) 
              AND STRPOS(lsad_name, ', WA') > 0
        GROUP BY lsad_name
    )
    SELECT 
           *, (area_sqkm * pop_density / 1000000) AS population_millions
    FROM urban_populations
    ORDER BY area_sqkm DESC
    LIMIT 10
    ```
     
     
