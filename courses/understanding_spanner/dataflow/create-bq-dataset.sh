#! /bin/sh
bq --location=us-central1 mk --dataset $GOOGLE_CLOUD_PROJECT:petsdb
bq mk --table petsdb.Pets OwnerID:STRING,PetName:STRING,PetType:STRING,Breed:STRING
