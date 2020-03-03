# loop through all parameters
while [ "$1" != "" ]; do
    case $1 in
      "--model-path")
        shift
        MODEL_PATH="$1"
        echo
        shift
        ;;
        "--model-name")
        shift
        MODEL_NAME="$1"
        echo
        shift
        ;;
        "--model-region")
        shift
        MODEL_REGION="$1"
        echo
        shift
        ;;
        "--model-version")
        shift
        MODEL_VERSION="$1"
        echo
        shift
        ;;
        "--model-runtime-version")
        shift
        RUNTIME_VERSION="$1"
        echo
        shift
        ;;
        "--model-prediction-class")
        shift
        MODEL_PREDICTION_CLASS="$1"
        echo
        shift
        ;;
        "--model-python-version")
        shift
        MODEL_PYTHON_VERSION="$1"
        echo
        shift
        ;;
        "--model-package-uris")
        shift
        MODEL_PACKAGE_URIS="$1"
        echo
        shift
        ;;
        *)
   esac
done

# echo inputs
echo MODEL_PATH               = "${MODEL_PATH}"
echo MODEL                    = "${MODEL_EXPORT_PATH}"
echo MODEL_NAME               = "${MODEL_NAME}"
echo MODEL_REGION             = "${MODEL_REGION}"
echo MODEL_VERSION            = "${MODEL_VERSION}"
echo RUNTIME_VERSION          = "${RUNTIME_VERSION}"
echo MODEL_PREDICTION_CLASS   = "${MODEL_PREDICTION_CLASS}"
echo MODEL_PYTHON_VERSION     = "${MODEL_PYTHON_VERSION}"
echo MODEL_PACKAGE_URIS       = "${MODEL_PACKAGE_URIS}"


# create model
modelname=$(gcloud ai-platform models list | grep -w "$MODEL_NAME")
echo "$modelname"
if [ -z "$modelname" ]; then
   echo "Creating model $MODEL_NAME in region $REGION"

   gcloud ai-platform models create ${MODEL_NAME} \
    --regions ${MODEL_REGION}
else
   echo "Model $MODEL_NAME already exists"
fi

# create version with custom prediction routine (beta)
echo "Creating version $MODEL_VERSION from $MODEL_PATH"
gcloud beta ai-platform versions create ${MODEL_VERSION} \
       --model ${MODEL_NAME} \
       --origin ${MODEL_PATH} \
       --python-version ${MODEL_PYTHON_VERSION} \
       --runtime-version ${RUNTIME_VERSION} \
       --package-uris ${MODEL_PACKAGE_URIS} \
       --prediction-class ${MODEL_PREDICTION_CLASS}