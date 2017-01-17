#!/bin/bash

USER=vlakshmanan   # change this ...

ROLE=$(/usr/share/google/get_metadata_value attributes/dataproc-role)
if [[ "${ROLE}" == 'Master' ]]; then

  cd home/$USER
  git clone https://github.com/GoogleCloudPlatform/training-data-analyst

fi
