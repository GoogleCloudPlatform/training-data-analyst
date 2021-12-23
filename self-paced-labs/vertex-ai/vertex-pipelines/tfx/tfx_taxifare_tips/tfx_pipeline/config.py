"""TFX pipeline configurations."""

import os
from tfx import v1 as tfx

GOOGLE_CLOUD_PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT_ID", "")
GOOGLE_CLOUD_REGION = os.getenv("GOOGLE_CLOUD_REGION", "")
GCS_LOCATION = os.getenv("GCS_LOCATION", "")

ARTIFACT_STORE_URI = os.path.join(GCS_LOCATION, "tfx-artifacts")
MODEL_REGISTRY_URI = os.path.join(GCS_LOCATION, "model-registry")

DATASET_DISPLAY_NAME = os.getenv("DATASET_DISPLAY_NAME", "chicago-taxifare-tips")
MODEL_DISPLAY_NAME = os.getenv("MODEL_DISPLAY_NAME", f"{DATASET_DISPLAY_NAME}-classifier")
PIPELINE_NAME = os.getenv("PIPELINE_NAME", f"{MODEL_DISPLAY_NAME}-train-pipeline")

ML_USE_COLUMN = "ml_use"
EXCLUDE_COLUMNS = ",".join(["trip_start_timestamp"])
TRAIN_LIMIT = os.getenv("TRAIN_LIMIT", "0")
TEST_LIMIT = os.getenv("TEST_LIMIT", "0")
SERVE_LIMIT = os.getenv("SERVE_LIMIT", "0")

NUM_TRAIN_SPLITS = os.getenv("NUM_TRAIN_SPLITS", "4")
NUM_EVAL_SPLITS = os.getenv("NUM_EVAL_SPLITS", "1")
ACCURACY_THRESHOLD = os.getenv("ACCURACY_THRESHOLD", "0.8")

USE_KFP_SA = os.getenv("USE_KFP_SA", "False")

TFX_IMAGE_URI = os.getenv(
    "TFX_IMAGE_URI", "us-central1-docker.pkg.dev/dougkelly-vertex-demos/tfx-taxifare-tips/tfx-taxifare-tips:latest"
)

BEAM_RUNNER = os.getenv("BEAM_RUNNER", "DirectRunner")
BEAM_DIRECT_PIPELINE_ARGS = [
    f"--project={GOOGLE_CLOUD_PROJECT_ID}",
    f"--temp_location={os.path.join(GCS_LOCATION, 'temp')}",
]
BEAM_DATAFLOW_PIPELINE_ARGS = [
    f"--project={GOOGLE_CLOUD_PROJECT_ID}",
    f"--temp_location={os.path.join(GCS_LOCATION, 'temp')}",
    f"--region={GOOGLE_CLOUD_REGION}",
    f"--runner={BEAM_RUNNER}",
]

TRAINING_RUNNER = os.getenv("TRAINING_RUNNER", "vertex")
VERTEX_TRAINING_ARGS = {
    "project": GOOGLE_CLOUD_PROJECT_ID,
    "worker_pool_specs": [
        {
            "machine_spec": {
                "machine_type": "n1-standard-4",
            },
            "replica_count": 1,
            "container_spec": {
                "image_uri": TFX_IMAGE_URI,
            },
        }
    ],
}

VERTEX_TRAINING_CONFIG = {
    tfx.extensions.google_cloud_ai_platform.ENABLE_UCAIP_KEY: True,
    tfx.extensions.google_cloud_ai_platform.UCAIP_REGION_KEY: GOOGLE_CLOUD_REGION,
    tfx.extensions.google_cloud_ai_platform.TRAINING_ARGS_KEY: VERTEX_TRAINING_ARGS,
    "use_gpu": False,
}

ENABLE_CACHE = os.getenv("ENABLE_CACHE", "0")

os.environ["GOOGLE_CLOUD_PROJECT_ID"] = GOOGLE_CLOUD_PROJECT_ID
os.environ["PIPELINE_NAME"] = PIPELINE_NAME
os.environ["TFX_IMAGE_URI"] = TFX_IMAGE_URI
os.environ["MODEL_REGISTRY_URI"] = MODEL_REGISTRY_URI
