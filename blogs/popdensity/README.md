Accompanies the blog post  "Querying geographic raster data in BigQuery the brute force way"

https://medium.com/google-cloud/querying-geographic-raster-data-in-bigquery-the-brute-force-way-1da46799d65f


Decide whether you want to load the NASA data or the SEDAC data.
The NASA file is smaller (10km resolution) and is what I recommend if you just want to try things out. The SEDAC file is 1km resolution and much more accurate, so do that if you want to use this to make real decisions.
Both datasets are global.

## Option 1: NASA

1. Download a 3600x1800 resolution CSV file from https://neo.sci.gsfc.nasa.gov/view.php?datasetId=SEDAC_POP
2. Assuming you saved it as popdensity.csv, run:
    ```
      ./convert_to_geo.py --format=nasa --input popdensity.csv
    ```
3. Change the BUCKET variable in the following script and run it:
     ```
      ./load_geo_into_bq.sh
    ```
    
## Option 2: SEDAC
1. Download 30-arcsec resolution ASCII file from https://sedac.ciesin.columbia.edu/data/set/gpw-v4-population-density-rev11/data-download
2. Unzip the downloaded file. You will have 8 tiles with the extension .asc.
3. To load in the global data, run:
    ```
       ./convert_to_geo.py --format=sedac --input gpw_*.asc
    ```
    If you want data for just Australia, you could load up only the tile that contains Australia:
    ```
       ./convert_to_geo.py --format=sedac --input gpw_*_8.asc
    ```
    If you want data for just the United States, you need only tiles 1 and 2, so you could do:
    ```
       ./convert_to_geo.py --format=sedac --input gpw_*_1.asc gpw_*_2.asc
    ```   
 4. Change the BUCKET variable in the following script and run it:
     ```
      ./load_geo_into_bq.sh
    ```   
  
