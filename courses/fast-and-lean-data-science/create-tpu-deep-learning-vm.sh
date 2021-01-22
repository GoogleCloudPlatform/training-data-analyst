#!/usr/bin/env bash

# please configure your login, project region and zone first by running gcloud init
# region us-central1 zone us-central1-b usually have TPUs available

DEFAULT_TF_VERSION="2.4" # WARNING: DLVM release is tf2-2-3-cpu but contains TF 2.3.1
IMAGE_FAMILY_PATTERN="tf2-2-x-cpu"

usage()
{
    echo "Usage: create-tpu-deep-learning-vm.sh vm-name [ --machine-type | --tpu-type | --help | --nightly | --version ]"
    echo "The default machine type is n1-standard-8."
    echo "The default TPU type is v2-8."
    echo "The default Tensorflow version is $DEFAULT_TF_VERSION."
    echo "Supported Tensorflow versions are 2.1, 2.2, 2.3, 2.3.1, 2.4 and nightly."
    echo "You can use \"--version nightly\" or \"--nightly\" to obtain a nightly version of Tensorflow on the VM and TPU."
    echo "Please run \"gcloud init\" befor this script to set your default zone."
    echo "Example:"
    echo "./create-tpu-deep-learning-vm.sh my-machine --tpu-type v3-8 --version 2.3"
}

maj_min_version() # params: version. Return: sets global variable "maj_min_version"
if [[ "$1" =~ ([0-9]*\.[0-9]*)\.[0-9]* ]]; # if there is sub-version like 2.3.1, cut the version to 2.3. DLVM images are always on the latest minor version.
    then
        maj_min_version=${BASH_REMATCH[1]}; # this keeps
    else
        maj_min_version="$1"
    fi

create_vm() # params: machine_name, machine_type, tfnightly, version
{
    extra_install=""
    if [ "$3" != 0 ]; # if tf-nighty requested
    then
        # since DLVM move to conda, system pip does not work for installing tf-nightly anymore
        extra_install="./opt/conda/bin/pip install tf-nightly; ./opt/conda/bin/pip install behave";
        maj_min_version $DEFAULT_TF_VERSION # result in variable "maj_min_version". No sub-minor TF versions in DLVM images.
        vm_version=$maj_min_version
        version_msg="tf-nightly (2.x)";
    else
        extra_install="./opt/conda/bin/pip install behave";
        maj_min_version "$4" # result in variable "maj_min_version". No sub-minor TF versions in DLVM images.
        vm_version=$maj_min_version
        version_msg="$4";s
    fi
    image_family=${IMAGE_FAMILY_PATTERN/2-x/${vm_version//./-}}
    echo "Creating VM named $1 of type $2 with Tensorflow $version_msg and image family $image_family. Check for it with \"gcloud compute instances list\""
    gcloud compute instances create $1 \
        --machine-type n1-standard-8 \
        --image-project deeplearning-platform-release \
        --image-family $image_family \
        --scopes cloud-platform \
        --metadata proxy-mode=project_editors,startup-script="echo \"export TPU_NAME=$1\" > /etc/profile.d/tpu-env.sh; $extra_install" \
        --async

    # To list all possible deep learning VM images:
    # gcloud compute images list --project deeplearning-platform-release
}

create_tpu() # params: machine_name, tpu_type, tfnightly, version
{
    if [ "$3" != 0 ];  # if tf-nighty requested
    then
        tpu_version="nightly";
    else
        tpu_version=$4
    fi
    echo "Creating TPU named $1 with Tensorflow $tpu_version. Check for it with \"gcloud compute tpus list\""
    gcloud compute tpus create $1 \
        --version $tpu_version \
        --accelerator-type $2
}


# standard parameter processing bash code with defaults
tfnightly=0
version=$DEFAULT_TF_VERSION
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
        --version )             shift
                                version=$1
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
if [ "$version" = "2.0" ] || [[ "$version" = 1*  ]]; then
    usage
    exit 1
fi
if [ "$version" = "nightly" ]; then
    tfnightly=1
fi

create_vm "$machine_name" "$machine_type" "$tfnightly" "$version"
create_tpu "$machine_name" "$tpu_type" "$tfnightly" "$version"


