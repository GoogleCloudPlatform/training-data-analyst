#!/bin/bash
cd /content
if [ ! -d "training-data-analyst" ]; then
   git clone http://github.com/GoogleCloudPlatform/training-data-analyst/
fi
