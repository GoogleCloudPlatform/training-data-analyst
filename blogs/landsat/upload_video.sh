#!/bin/bash

if test $# -lt 1; then
   echo "Usage: ./upload_ee.sh IMAGE_DIR"
   echo "e.g:   ./upload_ee.sh gs://cloud-training-demos/landsat/output"
   exit -1
fi

INDIR=$1
GCS_IMAGES=$(gsutil ls -r $INDIR | grep TIF)
EEUSER=vlakshmanan

collection=""
for GCS_IMAGE in $GCS_IMAGES; do
   BASE=$(echo $GCS_IMAGE | sed 's/gs:..//g' | sed 's/.TIF//g' | sed 's/\//_/g')
   assetid="users/$EEUSER/$BASE"
   echo "$GCS_IMAGE --> $assetid"
   earthengine upload image --asset_id $assetid $GCS_IMAGE
   collection=$collection" images.push(ee.Image(' $assetid').visualize(vizParams));"
done

echo "In code.earthengine.google.com check on progress of ingestion under Tasks. Once you have the image available under Assets, run this script:"
echo ""
echo "var palette = ['FFFFFF', 'CE7E45', 'DF923D', 'F1B555', 'FCD163', '99B718', '74A901',"
echo "               '66A000', '529400', '3E8601', '207401', '056201', '004C00', '023B01',"
echo "               '012E01', '011D01', '011301'];"
echo "var vizParams = {min: 0, max: 100, palette: palette};"
echo "var polygon = ee.Geometry.Rectangle([55.1, -20.85, 55.9, -21.4]);"
echo "var images = []"
echo "$collection"
echo "var collection = ee.ImageCollection(images);"
echo "Export.video.toDrive({ \
  collection: collection, \
  description: 'reunionee', \
  dimensions: 720, \
  framesPerSecond: 12, \
  region: polygon \
});"
