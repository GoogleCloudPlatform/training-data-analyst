#!/usr/bin/env bash

# please configure your login, project region and zone first by running gcloud init
# region us-central1 zone us-central1-b usually have TPUs available

DEFAULT_TF_VERSION="2.2"
DEFAULT_IMAGE_FAMILY="tf2-2-2-cpu"

usage()
{
    echo "usage: create-tpu-deep-learning-vm.sh vm-name [ --machine-type | --tpu-type | --help | --nightly ]"
    echo "the default machine type is n1-standard-8"
    echo "the default TPU type is v2-8"
    echo "the default Tensorflow version is $DEFAULT_TF_VERSION ($DEFAULT_IMAGE_FAMILY)"
}

create_vm() # params: machine_name, machine_type, tfnightly
{
    extra_install=""
    if [ "$3" != 0 ];
    then
        # since DLVM move to conda, system pip does not work for installing tf-nightly anymore
        extra_install="./opt/conda/bin/pip install tf-nightly; ./opt/conda/bin/pip install behave";
        version_msg="tf-nightly (2.x)";
    else
        version=$DEFAULT_TF_VERSION;
        version_msg=$DEFAULT_TF_VERSION;
    fi
    echo "Creating VM named $1 of type $2 with Tensorflow $version_msg. Check for it with \"gcloud compute instances list\""
    gcloud compute instances create $1 \
        --machine-type n1-standard-8 \
        --image-project deeplearning-platform-release \
        --image-family $DEFAULT_IMAGE_FAMILY \
        --scopes cloud-platform \
        --metadata proxy-mode=project_editors,startup-script="echo \"export TPU_NAME=$1\" > /etc/profile.d/tpu-env.sh; $extra_install" \
        --async

    # To list all possible deep learning VM images:
    # gcloud compute images list --project deeplearning-platform-release
}

create_tpu() # params: machine_name, tpu_type, tfnightly
{
    if [ "$3" != 0 ];
    then
        version="nightly";
    else
        version=$DEFAULT_TF_VERSION
    fi
    rng=$RANDOM
    rng=${rng:0:2}
    echo "Creating TPU named $1 on 192.168.$rng.0/29 with Tensorflow $version. Check for it with \"gcloud compute tpus list\""
    gcloud compute tpus create $1 \
        --network default \
        --range 192.168.$rng.0/29 \
        --version $version \
        --accelerator-type $2
}


# standard parameter processing bash code with defaults
tfnightly=0
tpu_type="v2-8"
machine_type="n1-standard-8"
machine_name=$1 # machine name always in first position
shift
while [ "$1" != "" ]; do
    case $1 in
        --machine-type )        shift
                                machine_type=$1
                                ;;
        --tpu-type )            shift
                                tpu_type=$1
                                ;;
        -h | --help )           usage
                                exit
                                ;;
        --nightly )             tfnightly=1
                                ;;
        * )                     usage
                                exit 1
    esac
    shift
done

# parameter checks
if [ "$machine_name" = "" ] || [[ "$machine_name" = -* ]]; then
    usage
    exit 1
fi

create_vm "$machine_name" "$machine_type" "$tfnightly"
create_tpu "$machine_name" "$tpu_type" "$tfnightly"


