#!/bin/bash

if [ "$#" -ne 1 ]; then
   echo "Usage:   ./run_locally.sh mainclass-basename"
   echo "Example: ./run_oncloud.sh Grep"
   exit
fi

MAIN=com.google.cloud.training.dataanalyst.javahelp.$1

~/apache-maven-3.3.9/bin/mvn compile -e exec:java -Dexec.mainClass=$MAIN
