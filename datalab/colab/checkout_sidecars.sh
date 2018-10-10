#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: ./checkout_sidecars.sh  content-root-directory"
    echo "   eg: ./checkout_sidecars.sh  courses/machine_learning/deepdive/03_tensorflow"
    exit
fi

DIR=$1
REPO=https://github.com/GoogleCloudPlatform/training-data-analyst
TOPDIR=`basename $REPO`


# Checks out just the files that are alongside this notebook
rm -rf $TOPDIR
git clone --depth 1 --no-checkout $REPO
cd $TOPDIR
git config core.sparseCheckout true
echo "$DIR/*"> .git/info/sparse-checkout
git checkout
cd ..

# Move the sidecar files into place
mv $TOPDIR/$DIR/* .
rm -rf $TOPDIR
rm *.ipynb  # let's not have the notebooks themselves on disk, just on Drive
