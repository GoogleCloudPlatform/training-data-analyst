#!/bin/bash

if test $# -lt 1; then
   echo "Usage: ./upload_ee.sh  IMAGE_LOCATION"
   echo "e.g:   ./upload_ee.sh gs://cloud-training-demos/landsat/LC81590732015102LGN00_ndvi.TIF"
   exit -1
fi

GCS_IMAGE=$1
EEUSER=vlakshmanan
BASE=$(basename "$GCS_IMAGE" | cut -d. -f1)

earthengine upload image --asset_id users/$EEUSER/$BASE $GCS_IMAGE

echo "In code.earthengine.google.com check on progress of ingestion under Tasks. Once you have the image available under Assets, run this script:"
echo ""
echo "var ndvi = ee.Image('users/$EEUSER/$BASE');"
echo "var palette = ['FFFFFF', 'CE7E45', 'DF923D', 'F1B555', 'FCD163', '99B718', '74A901',"
echo "               '66A000', '529400', '3E8601', '207401', '056201', '004C00', '023B01',"
echo "               '012E01', '011D01', '011301'];"
echo "var vizParams = {min: 0, max: 100, palette: palette};"
echo "Map.addLayer(ndvi, vizParams);"
echo "Map.centerObject(ndvi);"
