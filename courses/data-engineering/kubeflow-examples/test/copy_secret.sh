#!/bin/bash
#
# A simple script to copy a secret from 1 namespace to another
#
# Usage 
# copy_secret <source namepspace> <dest namespace> <secret name>
set -e
SOURCE=$1
DEST=$2
NAME=$3

usage() {
	echo copy_secret "<source namepspace> <dest namespace> <secret name>"
}

if [ -z ${SOURCE} ]; then
	usage
	exit -1
fi

if [ -z ${DEST} ]; then
	usage
	exit -1
fi

if [ -z ${NAME} ]; then
	usage
	exit -1
fi

echo getting secret
SECRET=$(kubectl -n ${SOURCE} get secrets user-gcp-sa -o jsonpath="{.data.${NAME}\.json}" | base64 -d)
kubectl create -n ${DEST} secret generic ${NAME} --from-literal="${NAME}.json=${SECRET}"