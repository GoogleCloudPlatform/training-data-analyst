#!/bin/bash
git clone https://github.com/tensorflow/tpu
for FILE in $(ls tpu/models/experimental/amoeba_net/); do
    CMD="cat tpu/models/experimental/amoeba_net/$FILE "
    for f2 in $(ls tpu/models/experimental/amoeba_net/); do
        MODULE=`echo $f2 | sed 's/.py//g'`
        CMD="$CMD | sed 's/import ${MODULE}/from . import ${MODULE}/g' "
    done
    CMD="$CMD > imgclass/trainer/$FILE"
    echo $CMD
    eval $CMD
done
