#!/bin/bash

if [ "$#" -lt 2 ]; then
   echo "Usage:  ./create_projects.sh  project-prefix  email1 [email2 [email3 ...]]]"
   echo "   eg:  ./create_projects.sh  learnml-20170106  somebody@gmail.com someother@gmail.com"
   exit
fi

gcloud components update
gcloud components install alpha

PROJECT_PREFIX=$1
shift
EMAILS=$@

for EMAIL in $EMAILS; do
   PROJECT_ID=$(echo "${PROJECT_PREFIX}-${EMAIL}" | sed 's/@/x/g' | sed 's/\./x/g' | cut -c 1-30)
   echo "Deleting project $PROJECT_ID for $EMAIL ... "

   gcloud alpha projects delete $PROJECT_ID
done
