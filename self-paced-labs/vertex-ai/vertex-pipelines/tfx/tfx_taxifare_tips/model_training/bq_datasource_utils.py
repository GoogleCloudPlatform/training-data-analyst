"""Utilities for generating BigQuery data querying scirpts."""
from google.cloud import aiplatform as vertex_ai


def _get_source_query(bq_dataset_name, bq_table_name, ml_use, limit=None):
    """
    Args:
      bq_dataset_name(str):
      bq_table_name(str):
      ml_use:
      limit:
    Returns:
      query(str):
    """
    query = """
    SELECT 
        IF(trip_month IS NULL, -1, trip_month) trip_month,
        IF(trip_day IS NULL, -1, trip_day) trip_day,
        IF(trip_day_of_week IS NULL, -1, trip_day_of_week) trip_day_of_week,
        IF(trip_hour IS NULL, -1, trip_hour) trip_hour,
        IF(trip_seconds IS NULL, -1, trip_seconds) trip_seconds,
        IF(trip_miles IS NULL, -1, trip_miles) trip_miles,
        IF(payment_type IS NULL, 'NA', payment_type) payment_type,
        IF(pickup_grid IS NULL, 'NA', pickup_grid) pickup_grid,
        IF(dropoff_grid IS NULL, 'NA', dropoff_grid) dropoff_grid,
        IF(euclidean IS NULL, -1, euclidean) euclidean,
        IF(loc_cross IS NULL, 'NA', loc_cross) loc_cross"""
    if ml_use:
        query += f""",
        tip_bin
    FROM {bq_dataset_name}.{bq_table_name} 
    WHERE ml_use = '{ml_use}'
    """
    else:
        query += f"""
    FROM {bq_dataset_name}.{bq_table_name} 
    """
    if limit:
        query += f"LIMIT {limit}"

    return query


def get_training_source_query(
    project, region, dataset_display_name, ml_use, limit=None
):
    """
    Args:
      project(str):
      region(str):
      dataset_display_name:
      ml_use:
      limit:
    Returns:
      query(str):
    """
    vertex_ai.init(project=project, location=region)

    dataset = vertex_ai.TabularDataset.list(
        filter=f"display_name={dataset_display_name}", order_by="update_time"
    )[-1]
    bq_source_uri = dataset.gca_resource.metadata["inputConfig"]["bigquerySource"][
        "uri"
    ]
    _, bq_dataset_name, bq_table_name = bq_source_uri.replace("g://", "").split(".")

    return _get_source_query(bq_dataset_name, bq_table_name, ml_use, limit)
