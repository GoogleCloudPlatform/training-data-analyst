#!/bin/bash

. $(cd $(dirname $BASH_SOURCE) && pwd)/env.sh

BUCKET=$PROJECT_ID

$SCRIPTS_DIR/run.sh --bucket $BUCKET
