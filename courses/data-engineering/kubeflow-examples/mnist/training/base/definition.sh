#!/bin/bash 

# The script is to define the number of Ps and Workers for TFJOB.
# Usage: definition.sh --numPs number_of_PS --numWorkers number_of_worker

while (($#)); do
   case $1 in
     "--numPs")
       shift
       numPs="$1"
       shift
       ;;
     "--numWorkers")
       shift
       numWorkers="$1"
       shift
       ;;
     "--help")
       shift
       echo "Usage: definition.sh --numPs number_of_PS --numWorkers number_of_worker"
       shift
       ;;
     *)
       echo "Unknown argument: '$1'"
       echo "Usage: definition.sh --numPs number_of_PS --numWorkers number_of_worker"
       exit 1
       ;;
   esac
done

BASE_PATH=$(dirname "$0")

if [ "x${numPs}" != "x" ]; then
  if [[ ${numPs} =~ ^[0-9]+$ ]] && [ ${numPs} -gt 0 ]; then
    (cd ${BASE_PATH}; sed -i.sedbak s/%numPs%/${numPs}/  Ps.yaml >> /dev/null)
    (cd ${BASE_PATH}; kustomize edit add patch Ps.yaml)
    sed -i.sedbak '/patchesJson6902/a \
- path: Ps_patch.yaml \
\  target: \
\     group: kubeflow.org \
\     kind: TFJob \
\     name: \$(trainingName) \
\     version: v1 \
\      
' kustomization.yaml
  else
    echo "ERROR: numPS must be an integer greater than or equal to 1."
    exit 1
  fi 
fi

if [ "x${numWorkers}" != "x" ]; then
  if [[ ${numWorkers} =~ ^[0-9]+$ ]] && [ ${numWorkers} -gt 0 ]; then
    (cd ${BASE_PATH}; sed -i.sedbak s/%numWorkers%/${numWorkers}/ Worker.yaml >> /dev/null)
    (cd ${BASE_PATH}; kustomize edit add patch Worker.yaml)
    sed -i.sedbak '/patchesJson6902/a \
- path: Worker_patch.yaml \
\  target: \
\     group: kubeflow.org \
\     kind: TFJob \
\     name: \$(trainingName) \
\     version: v1 \
\      
' kustomization.yaml
  else
    echo "ERROR: numWorkers must be an integer greater than or equal to 1."
    exit 1
  fi
fi

rm -rf ${BASE_PATH}/*.sedbak
rm -rf *.sedbak
