#!/bin/bash

if [ "$#" -lt 2 ]; then
   echo "Usage:  ./create_projects.sh  project-prefix  email1 [email2 [email3 ...]]]"
   echo "   eg:  ./create_projects.sh  learnml-20170106  somebody@gmail.com someother@gmail.com"
   exit
fi

PROJECT_PREFIX=$1
shift
EMAILS=$@

gcloud components update
gcloud components install alpha

for EMAIL in $EMAILS; do
   PROJECT_ID=$(echo "${PROJECT_PREFIX}-${EMAIL}" | sed 's/@/-/g' | sed 's/\./-/g' | cut -c 1-30)
   echo "Creating project $PROJECT_ID for $EMAIL ... "

   gcloud alpha projects create $PROJECT_ID
   gcloud alpha projects get-iam-policy $PROJECT_ID --format=json > iam.json.orig
   cat iam.json.orig | sed s'/"bindings": \[/"bindings": \[ \{"members": \["user:'$EMAIL'"\],"role": "roles\/editor"\},/g' > iam.json.new
   gcloud alpha projects set-iam-policy $PROJECT_ID iam.json.new

done
