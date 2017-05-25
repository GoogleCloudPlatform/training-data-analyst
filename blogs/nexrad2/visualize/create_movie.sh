#!/bin/bash
rm -rf images
mkdir images
for volumefile in $(ls data); do
    base=$(basename $volumefile)
    python plot_pngs.py data/$volumefile images/$base.png
done
