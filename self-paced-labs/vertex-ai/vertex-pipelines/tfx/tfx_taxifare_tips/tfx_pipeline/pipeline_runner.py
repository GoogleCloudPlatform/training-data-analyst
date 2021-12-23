"""Define KubeflowV2DagRunner to run the training pipeline using Vertex Pipelines."""
import os
import logging
from tfx.v1.orchestration.experimental import (
    KubeflowV2DagRunner,
    KubeflowV2DagRunnerConfig,
)


from tfx_taxifare_tips.tfx_pipeline import config
from tfx_taxifare_tips.tfx_pipeline import pipeline


def compile_training_pipeline(pipeline_definition_file):
    """Following function will write the pipeline definition to PIPELINE_DEFINITION_FILE.
    Args:
      pipeline_definition_file(str):
    Returns:
      pipeline_definition_file(json):
    """

    pipeline_root = os.path.join(
        config.ARTIFACT_STORE_URI,
        config.PIPELINE_NAME,
    )
    
    logging.info("pipeline_root: %s", pipeline_root)
    logging.info("tfx_image_uri: %s", config.TFX_IMAGE_URI)

    managed_pipeline = pipeline.create_pipeline(
        pipeline_name=config.PIPELINE_NAME, pipeline_root=pipeline_root
    )
    
    logging.info("pipeline_info: %s", str(managed_pipeline.pipeline_info))
    

    runner = KubeflowV2DagRunner(
        config=KubeflowV2DagRunnerConfig(default_image=config.TFX_IMAGE_URI),
        output_filename=pipeline_definition_file,
    )

    return runner.run(managed_pipeline, write_out=True)
