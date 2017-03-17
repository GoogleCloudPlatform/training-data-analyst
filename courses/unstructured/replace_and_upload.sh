#!/bin/sh

if [ "$#" -ne 1 ]; then
   echo "Usage:  ./replace_and_upload.sh bucket-name"
   exit
fi

BUCKET=$1
echo "replacing bucket references to $BUCKET and copying to gs://$BUCKET/unstructured"

# replace
TEMP=tmp
rm -rf $TEMP
mkdir $TEMP
for FILE in $(ls -1 *.py *.ipynb); do
    echo $FILE
    cat $FILE | sed "s/BUCKET_NAME/$BUCKET/g" > $TEMP/$FILE
done 

# first the originals, then the modified
gsutil -m cp * gs://$BUCKET/unstructured
gsutil -m cp $TEMP/* gs://$BUCKET/unstructured
