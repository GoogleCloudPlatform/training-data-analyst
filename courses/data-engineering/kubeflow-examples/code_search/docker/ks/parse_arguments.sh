#!/bin/bash
# Common logic to parse the argument
# To use it, define the usage() function for help message and name array variables for required arguments in the
# parent script

parseArgs() {
  # Parse all command line options
  while [[ $# -gt 0 ]]; do
    # Parameters should be of the form
    # --{name}=${value}
    echo parsing "$1"
    if [[ $1 =~ ^--(.*)=(.*)$ ]]; then
    	name=${BASH_REMATCH[1]}
    	value=${BASH_REMATCH[2]}
     	eval ${name}="${value}"
    elif [[ $1 =~ ^--(.*)$ ]]; then
		name=${BASH_REMATCH[1]}
		value=true
		eval ${name}="${value}"
    else
    	echo "Argument $1 did not match the pattern --{name}={value} or --{name}"
    fi
    shift
  done
}

parseArgs $*

missingParam=false
for i in ${names[@]}; do
	if [ -z ${!i} ]; then
		echo "--${i} not set"
		missingParam=true
	fi
done
 if ${missingParam}; then
	usage
	exit 1
fi
