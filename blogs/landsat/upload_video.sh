#!/bin/bash

if test $# -lt 1; then
   echo "Usage: ./upload_ee.sh GCS_IMAGE_DIR"
   echo "e.g:   ./upload_ee.sh gs://cloud-training-demos/landsat/output2015"
   exit -1
fi

INDIR=$1
GCS_IMAGES=$(gsutil ls -r $INDIR | grep TIF)
EEUSER=vlakshmanan

collection=users/$EEUSER/reunionvideo
earthengine create collection $collection

for GCS_IMAGE in $GCS_IMAGES; do
   BASE=$(echo $GCS_IMAGE | sed 's/gs:..//g' | sed 's/.TIF//g' | sed 's/\//_/g')
   assetid="$collection/$BASE"
   echo "$GCS_IMAGE --> $assetid"
   earthengine upload image --nodata_value 255 --asset_id $assetid $GCS_IMAGE
done

echo "Use this script in earthengine to export a video:

var palette = ['FFFFFF', 'CE7E45', 'DF923D', 'F1B555', 'FCD163', '99B718', '74A901',
               '66A000', '529400', '3E8601', '207401', '056201', '004C00', '023B01',
               '012E01', '011D01', '011301'];
var vizParams = {min: 0, max: 100, palette: palette};
var polygon = ee.Geometry.Rectangle([55.1, -20.85, 55.9, -21.4]);

var collection = ee.ImageCollection('users/$EEUSER/reunionvideo');

var withMonths = collection.map(function(image) {
  var groups = image.id().match('LC8......(....)(...)....._ndvi');
  var year = ee.Number.parse(groups.get(1));
  var doy = ee.Number.parse(groups.get(2));
  var date = ee.Date.fromYMD(year, 1, 1).advance(doy.subtract(1), 'day');
  return image.set('month', date.get('month'));
});

var monthlyImages = ee.List.sequence(1, 12).map(function(month) {
  return withMonths.filter(ee.Filter.equals('month', month))
    .max().visualize(vizParams);
});

Export.video.toDrive({
  collection: ee.ImageCollection(monthlyImages),
  description: 'reunionee',
  dimensions: 720,
  framesPerSecond: 12,
  region: polygon,
});

"
