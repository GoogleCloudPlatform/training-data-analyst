#!/bin/sh
# Check https://cloud.google.com/compute/docs/gpus/ for K-80
./run_dv.sh \
       us-central1-c  \
       ./dv_rice.yaml \
       ERS467753 \
       gs://rice-3k/reference/Os-Nipponbare-Reference-IRGSP-1.0/Os-Nipponbare-Reference-IRGSP-1.0.fa \
       gs://rice-3k/tmp/ERS467753.bam
       

#gs://rice-3k/PRJEB6180/aligned-Os-Nipponbare-Reference-IRGSP-1.0/ERS467753.bam
