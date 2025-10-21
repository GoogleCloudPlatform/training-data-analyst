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
for FILE in $(ls -1 *.py *.ipynb init*.sh); do
    echo $FILE
    cat $FILE | sed "s/BUCKET_NAME/$BUCKET/g" | sed "s/USER_NAME/$USER/g" > $TEMP/$FILE
done 

# first the originals, then the modified
gcloud storage cp * gs://$BUCKET/unstructured
gcloud storage cp $TEMP/* gs://$BUCKET/unstructured

# photos ...
gcloud storage cp photos/* gs://$BUCKET/unstructured/photos
gcloud storage objects update --add-acl-grant=entity=allUsers,role=READER gs://$BUCKET/unstructured/photos/*

# this allows you to look at the .py file in a browser
gcloud storage objects update --content-type="text/plain" gs://$BUCKET/unstructured/*.py
