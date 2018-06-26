#!/bin/bash
rm -rf tpu
git clone https://github.com/tensorflow/tpu
cd tpu
TFVERSION=$1
echo "Switching to version r$TFVERSION"
git checkout r$TFVERSION
cd ..
  
MODELCODE=tpu/models/official/resnet
OUTDIR=mymodel
rm -rf $OUTDIR

# preprocessing
cp -r imgclass $OUTDIR   # brings in setup.py and __init__.py
cp tpu/tools/datasets/jpeg_to_tf_record.py $OUTDIR/trainer/preprocess.py

# model: fix imports
for FILE in $(ls -p $MODELCODE | grep -v /); do
    CMD="cat $MODELCODE/$FILE "
    for f2 in $(ls -p $MODELCODE | grep -v /); do
        MODULE=`echo $f2 | sed 's/.py//g'`
        CMD="$CMD | sed 's/^import ${MODULE}/from . import ${MODULE}/g' "
    done
    CMD="$CMD > $OUTDIR/trainer/$FILE"
    eval $CMD
done
find $OUTDIR
echo "Finished copying files into $OUTDIR"