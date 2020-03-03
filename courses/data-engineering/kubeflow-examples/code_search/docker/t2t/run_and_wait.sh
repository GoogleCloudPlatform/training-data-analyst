#!/usr/bin/env bash
# This script is a wrapper script for T2T.
# T2T doesn't respect TF_CONFIG; instead it relies on command line variables.
# So this script parses TF_CONFIG and then appends appropriate command line arguments
# to whatever command was entered.
set -ex
env | sort
echo running "$@"
"$@" 

# Sleep to give fluentd time to capture logs
sleep 120
