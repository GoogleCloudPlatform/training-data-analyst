Accompanies the blog post  "Querying geographic raster data in BigQuery the brute force way"

https://medium.com/google-cloud/querying-geographic-raster-data-in-bigquery-the-brute-force-way-1da46799d65f


(1) First download data from either NASA or SEDAC


(2) Then, run:
      ./convert_to_geo.py --format=nasa --input popdensity.csv
    OR
      ./convert_to_geo.py --format=sedac --input gpw_v4_population_density*.asc

(3) Then, run:
      ./load_geo_into_bq.sh
