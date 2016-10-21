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
echo "Map.addLayer(ndvi);"
echo "Map.centerObject(ndvi);"
