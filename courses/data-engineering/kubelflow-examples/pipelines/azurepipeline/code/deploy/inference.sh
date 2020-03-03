#!/bin/bash
while getopts "n:w:g:" option;
    do
    case "$option" in
        n ) DEPLOYMENT_NAME=${OPTARG};;
        w ) WORKSPACE=${OPTARG};;
        g ) RESOURCE_GROUP=${OPTARG};;
    esac
done
echo "test the deployment with a burrito image"
az ml service run -n ${DEPLOYMENT_NAME} -d '{ "image": "https://www.exploreveg.org/files/2015/05/sofritas-burrito.jpeg" }' -w ${WORKSPACE} -g ${RESOURCE_GROUP}
echo "test the deployment with a taco image"
az ml service run -n ${DEPLOYMENT_NAME} -d '{ "image": "https://c1.staticflickr.com/5/4022/4401140214_f489c708f0_b.jpg" }' -w ${WORKSPACE} -g ${RESOURCE_GROUP}
