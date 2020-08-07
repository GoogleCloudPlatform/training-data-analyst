#!/bin/bash

. $(cd $(dirname $BASH_SOURCE) && pwd)/env.sh

COMPONENT_YAML_TEMPL=$COMPONENT_DIR/component.template.yaml
COMPONENT_YAML=$COMPONENT_DIR/component.yaml

cat $COMPONENT_YAML_TEMPL | sed  "s/PROJECT/$PROJECT_ID/" > $COMPONENT_YAML
