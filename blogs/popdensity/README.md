Accompanies the blog post  "Querying geographic raster data in BigQuery the brute force way"

https://medium.com/google-cloud/querying-geographic-raster-data-in-bigquery-the-brute-force-way-1da46799d65f


(1) First download data from either NASA or SEDAC
The NASA file is smaller and is what I recommend if you just want to try things out. The SEDAC file is 1km resolution and much more accurate, so do that if you want to use this to make real decisions.
  * If NASA: Download a 3600x1800 resolution CSV file from https://neo.sci.gsfc.nasa.gov/view.php?datasetId=SEDAC_POP
    Save it as popdensity.csv and invoke this program specifying --format=nasa
  * If SEDAC: Download 30-arcsec resolution ASCII file from https://sedac.ciesin.columbia.edu/data/set/gpw-v4-population-density-rev11/data-download
    Unzip the downloaded file and invoke this program specifying --format=sedac


(2) Then, run:
      ./convert_to_geo.py --format=nasa --input popdensity.csv
    OR
      ./convert_to_geo.py --format=sedac --input gpw_v4_population_density*.asc

(3) Then, change the BUCKET variable in the following script and run it:
      ./load_geo_into_bq.sh
