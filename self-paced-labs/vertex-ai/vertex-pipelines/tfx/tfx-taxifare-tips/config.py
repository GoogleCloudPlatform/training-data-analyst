"""TFX pipeline configurations."""

import os

GOOGLE_CLOUD_PROJECT = os.getenv("PROJECT", "")
GOOGLE_CLOUD_REGION = os.getenv("REGION", "")
GCS_LOCATION = os.getenv("GCS_LOCATION", "")