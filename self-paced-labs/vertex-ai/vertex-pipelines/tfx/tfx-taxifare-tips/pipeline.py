"""Pipeline definition code."""
import tensorflow_model_analysis as tfma
from tfx.v1.extensions.google_cloud_big_query import BigQueryExampleGen
from tfx.v1.extensions.google_cloud_ai_platform import Trainer as VertexTrainer
from tfx.v1.extensions.google_cloud_ai_platform import Pusher as VertexPusher
from tfx.dsl.components.common.importer import Importer
from tfx.dsl.components.common.resolver import Resolver
from tfx.dsl.experimental import latest_artifacts_resolver
from tfx.dsl.experimental import latest_blessed_model_resolver
from tfx.v1.components import (
    StatisticsGen,
    ExampleValidator,
    Transform,
    Evaluator,
    Pusher
)

def create_pipeline(
    pipeline_root: str,):
    """
    Args:
    Returns:
    """
    
    
    
    # Configure train and eval splits for model training and evaluation.
    train_output_config = example_gen_pb2.Output(
        split_config=example_gen_pb2.SplitConfig(
            splits=[
                example_gen_pb2.SplitConfig.Split(
                    name="train", hash_buckets=int(config.NUM_TRAIN_SPLITS)
                ),
                example_gen_pb2.SplitConfig.Split(
                    name="eval", hash_buckets=int(config.NUM_EVAL_SPLITS)
                ),
            ]
        )
    )    
    
    # Generate train split examples.
    train_example_gen = BigQueryExampleGen(
        query=train_sql_query,
        output_config=train_output_config,
    ).with_id("TrainDataGen")
    
    # Generate dataset statistics.
    statistics_gen = StatisticsGen(examples=train_example_gen.outputs["examples"]).with_id(
        "StatisticsGen"
    )
    
    # Example validation.
    example_validator = ExampleValidator(
        statistics=statistics_gen.outputs["statistics"],
        schema=schema_importer.outputs["result"],
    ).with_id("ExampleValidator")
    
    
    # Data transformation.
    transform = Transform(
        examples=train_example_gen.outputs["examples"],
        schema=schema_importer.outputs["result"],
        module_file=TRANSFORM_MODULE_FILE,
        # This is a temporary workaround to run on Dataflow.
        force_tf_compat_v1=config.BEAM_RUNNER == "DataflowRunner",
        splits_config=transform_pb2.SplitsConfig(
            analyze=["train"], transform=["train", "eval"]
        ),
    ).with_id("Tranform")
    
    # Add dependency from example_validator to transform.
    transform.add_upstream_node(example_validator)
    
    # Train model on Vertex AI.
    trainer = VertexTrainer(
            module_file=TRAIN_MODULE_FILE,
            examples=transform.outputs["transformed_examples"],
            schema=schema_importer.outputs["result"],
            transform_graph=transform.outputs["transform_graph"],
            hyperparameters=hyperparams_gen.outputs["hyperparameters"],
            custom_config=config.VERTEX_TRAINING_CONFIG
        ).with_id("ModelTrainer")
    
    
    # Get the latest blessed model (baseline) for model validation.
    baseline_model_resolver = Resolver(
        strategy_class=latest_blessed_model_resolver.LatestBlessedModelResolver,
        model=Channel(type=standard_artifacts.Model),
        model_blessing=Channel(type=standard_artifacts.ModelBlessing),
    ).with_id("BaselineModelResolver")
    
    # Prepare evaluation config.
    eval_config = tfma.EvalConfig(
        model_specs=[
            tfma.ModelSpec(
                signature_name="serving_tf_example",
                label_key=features.TARGET_FEATURE_NAME,
                prediction_key="probabilities",
            )
        ],
        slicing_specs=[
            tfma.SlicingSpec(),
        ],
        metrics_specs=[
            tfma.MetricsSpec(
                metrics=[
                    tfma.MetricConfig(class_name="ExampleCount"),
                    tfma.MetricConfig(
                        class_name="BinaryAccuracy",
                        threshold=tfma.MetricThreshold(
                            value_threshold=tfma.GenericValueThreshold(
                                lower_bound={"value": float(config.ACCURACY_THRESHOLD)}
                            ),
                            # Change threshold will be ignored if there is no
                            # baseline model resolved from MLMD (first run).
                            change_threshold=tfma.GenericChangeThreshold(
                                direction=tfma.MetricDirection.HIGHER_IS_BETTER,
                                absolute={"value": -1e-10},
                            ),
                        ),
                    ),
                ]
            )
        ],
    )

    # Model evaluation.
    evaluator = Evaluator(
        examples=test_example_gen.outputs["examples"],
        example_splits=["test"],
        model=trainer.outputs["model"],
        baseline_model=baseline_model_resolver.outputs["model"],
        eval_config=eval_config,
        schema=schema_importer.outputs["result"],
    ).with_id("ModelEvaluator")
    

    # Push custom model to model registry.
    pusher = Pusher(
        model=trainer.outputs["model"],
        model_blessing=evaluator.outputs["blessing"],
        push_destination=push_destination,
    ).with_id("ModelPusher")
    
    
    pipeline_components = [
        train_example_gen,
        statistics_gen,
        example_validator,
        transform,
        trainer,
        baseline_model_resolver,
        evaluator,
        pusher
    ]
    
    return pipeline.Pipeline(
        pipeline_name=config.PIPELINE_NAME,
        pipeline_root=pipeline_root,
        components=pipeline_components,
        beam_pipeline_args=beam_pipeline_args,
        metadata_connection_config=metadata_connection_config,
        enable_cache=int(config.ENABLE_CACHE),
    )
