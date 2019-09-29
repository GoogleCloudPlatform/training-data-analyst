#!/bin/bash

. $(cd $(dirname $BASH_SOURCE) && pwd)/env.sh

COMPONENT_YAML=$COMPONENT_DIR/component.yaml

cat $COMPONENT_YAML | sed  "s/PROJECT/$PROJECT_ID/" > $COMPONENT_YAML 
