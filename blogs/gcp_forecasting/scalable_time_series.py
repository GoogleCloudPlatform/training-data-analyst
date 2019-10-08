"""Queries for scalable time-series modeling."""

def create_date_range(project, dataset_name, table_name):
    sql_date_range = """
WITH
  # Get min and max dates so we can enumerate the range next
  CTE_date_limits AS (
  SELECT
    CAST(MIN(sale_date) AS DATE) AS min_sale_date,
    CAST(MAX(sale_date) AS DATE) AS max_sale_date
  FROM
    `{0}.{1}.{2}` ),
  # Expand date range using date bounds
  CTE_date_range AS (
  SELECT
    UNIX_DATE(calendar_date) AS unix_date
  FROM
    UNNEST(GENERATE_DATE_ARRAY((
        SELECT
          min_sale_date
        FROM
          CTE_date_limits), (
        SELECT
          max_sale_date
        FROM
          CTE_date_limits), INTERVAL 1 DAY) ) AS calendar_date ),
  # Create start and end date ranges for timescale
  CTE_start_end_timescale_date_range AS (
  SELECT
    ROW_NUMBER() OVER (ORDER BY unix_date) - 1 AS timescale_idx,
    unix_date AS unix_timescale_start_date,
    LEAD(unix_date, 6) OVER (ORDER BY unix_date) AS unix_timescale_end_date
  FROM
    CTE_date_range )
    
  SELECT
    timescale_idx,
    unix_timescale_start_date,
    unix_timescale_end_date,
    DATE_FROM_UNIX_DATE(unix_timescale_start_date) AS timescale_start_date,
    DATE_FROM_UNIX_DATE(unix_timescale_end_date) AS timescale_end_date
  FROM
    CTE_start_end_timescale_date_range
    """.format(project, dataset_name, table_name)
    
    return sql_date_range

def bq_create_rolling_features_label(project, dataset, date_range_table, sales_dataset_table, value_name, downsample_size, window_size, horizon, labels_size=1):
    feature_pivot_list = ["""SUM(CASE WHEN timestep_idx = {time} - 1 THEN {value_name} ELSE 0.0 END) AS price_ago_{time}""".format(time=time,value_name=value_name) for time in range(window_size, 0, -1)]
    label_pivot_list = ["""SUM(CASE WHEN timestep_idx = {time} - 1 THEN {value_name} ELSE 0.0 END) AS price_ahead_{time}""".format(time=time,value_name=value_name) for time in range(1, labels_size + 1)]

    feature_list = ["price_ago_{time}".format(time=time) for time in range(window_size, 0, -1)]
    label_list = ["price_ahead_{time}".format(time=time) for time in range(1, labels_size + 1)]
    new_line = ",\n    "

    sql_bqml_sub_sequences = """
WITH
  # Create sequence date ranges
  CTE_seq_date_ranges AS (
  SELECT
    A.timescale_idx AS seq_idx,
    ROW_NUMBER() OVER (PARTITION BY A.timescale_idx ORDER BY B.unix_timescale_start_date) - 1 AS timestep_idx,
    B.timescale_idx AS timescale_idx,
    A.unix_timescale_start_date AS seq_unix_start_date,
    B.unix_timescale_start_date AS timestep_unix_start_date,
    B.unix_timescale_end_date AS timestep_unix_end_date
  FROM
    `{project}.{dataset}.{date_range_table}` AS A
  INNER JOIN
    `{project}.{dataset}.{date_range_table}` AS B
  ON
    MOD(B.unix_timescale_start_date - A.unix_timescale_start_date, {downsample_size}) = 0
    AND B.unix_timescale_start_date >= A.unix_timescale_start_date
  WHERE
    B.unix_timescale_end_date IS NOT NULL),
  # Create sequence date ranges for features data
  CTE_seq_features_date_range AS (
  SELECT
    *
  FROM
    CTE_seq_date_ranges
  WHERE
    timestep_idx < {window_size}),
  # Create sequence date ranges for labels data
  CTE_seq_labels_date_range AS (
  SELECT
    *
  FROM
    CTE_seq_date_ranges
  WHERE
    timestep_idx < {labels_size}),
  # Join timescale information with data to be aggregated over timescale
  CTE_timescale_joined_data AS (
  SELECT
    timescale_idx,
    unix_timescale_start_date,
    unix_timescale_end_date,
    all_sales.sale_price
  FROM
    `{project}.{dataset}.{date_range_table}` AS start_end_timescale_date_range
  INNER JOIN
    `{project}.{sales_dataset_table}` AS all_sales
  ON
    start_end_timescale_date_range.unix_timescale_start_date <= UNIX_DATE(CAST(all_sales.sale_date AS DATE))
    AND UNIX_DATE(CAST(all_sales.sale_date AS DATE)) <= start_end_timescale_date_range.unix_timescale_end_date),
  # Group data we want aggregated over timescale
  CTE_grouped_data AS (
  SELECT
    timescale_idx,
    unix_timescale_start_date,
    unix_timescale_end_date,
    APPROX_QUANTILES(sale_price, 100)[
  OFFSET
    (50)] AS {value_name}
  FROM
    CTE_timescale_joined_data
  GROUP BY
    timescale_idx,
    unix_timescale_start_date,
    unix_timescale_end_date),
  # Join features data to features date ranges
  CTE_features AS (
  SELECT
    A.seq_idx,
    A.timestep_idx,
    A.seq_unix_start_date,
    IFNULL(B.{value_name},0) AS {value_name}
  FROM
    CTE_seq_features_date_range AS A
  INNER JOIN
    CTE_grouped_data AS B
  ON
    A.timescale_idx = B.timescale_idx),
  # Aggregate features data into sequences
  CTE_seq_features AS (
  SELECT
    seq_idx,
    seq_unix_start_date,
    {feature_pivot_list}
  FROM
    CTE_features
  GROUP BY
    seq_idx,
    seq_unix_start_date),
  # Join labels data to labels date ranges
  CTE_labels AS (
  SELECT
    A.seq_idx,
    A.timestep_idx,
    A.seq_unix_start_date,
    IFNULL(B.{value_name},0) AS {value_name}
  FROM
    CTE_seq_labels_date_range AS A
  INNER JOIN
    CTE_grouped_data AS B
  ON
    A.timescale_idx = B.timescale_idx),
  # Aggregate labels data into sequences
  CTE_seq_labels AS (
  SELECT
    seq_idx,
    seq_unix_start_date,
    {label_pivot_list}
  FROM
    CTE_labels
  GROUP BY
    seq_idx,
    seq_unix_start_date)
  # Join features with labels with horizon in between
  SELECT
    DATE_FROM_UNIX_DATE(A.seq_unix_start_date) AS feat_seq_start_date,
    DATE_FROM_UNIX_DATE(A.seq_unix_start_date + {window_size} * {downsample_size} - 1) AS feat_seq_end_date,
    DATE_FROM_UNIX_DATE(B.seq_unix_start_date) AS lab_seq_start_date,
    DATE_FROM_UNIX_DATE(B.seq_unix_start_date + {labels_size} * {downsample_size} - 1) AS lab_seq_end_date,
    {feature_list},
    {label_list}
  FROM
    CTE_seq_features AS A
  INNER JOIN
    CTE_seq_labels AS B
  ON
    A.seq_unix_start_date + ({window_size} * {downsample_size} - 1) + ({downsample_size} * {horizon}) = B.seq_unix_start_date
  ORDER BY
    A.seq_idx
    """.format(project=project,
               dataset=dataset,
               date_range_table=date_range_table,
               sales_dataset_table=sales_dataset_table,
               value_name=value_name,
               downsample_size=downsample_size,
               window_size=window_size,
               horizon=horizon,
               labels_size=labels_size,
               feature_pivot_list=new_line.join(feature_pivot_list), 
               label_pivot_list=new_line.join(label_pivot_list), 
               feature_list=new_line.join(feature_list), 
               label_list=new_line.join(label_list))

    return sql_bqml_sub_sequences


def csv_create_rolling_features_label(project, dataset, date_range_table, sales_dataset_table, value_name, downsample_size, window_size, horizon, labels_size=1):
    sql_csv_sub_sequences = """
WITH
  # Create sequence date ranges
  CTE_seq_date_ranges AS (
  SELECT
    A.timescale_idx AS seq_idx,
    ROW_NUMBER() OVER (PARTITION BY A.timescale_idx ORDER BY B.unix_timescale_start_date) - 1 AS timestep_idx,
    B.timescale_idx AS timescale_idx,
    A.unix_timescale_start_date AS seq_unix_start_date,
    B.unix_timescale_start_date AS timestep_unix_start_date,
    B.unix_timescale_end_date AS timestep_unix_end_date
  FROM
    `{project}.{dataset}.{date_range_table}` AS A
  INNER JOIN
    `{project}.{dataset}.{date_range_table}` AS B
  ON
    MOD(B.unix_timescale_start_date - A.unix_timescale_start_date, {downsample_size}) = 0
    AND B.unix_timescale_start_date >= A.unix_timescale_start_date
  WHERE
    B.unix_timescale_end_date IS NOT NULL),
  # Create sequence date ranges for features data
  CTE_seq_features_date_range AS (
  SELECT
    *
  FROM
    CTE_seq_date_ranges
  WHERE
    timestep_idx < {window_size}),
  # Create sequence date ranges for labels data
  CTE_seq_labels_date_range AS (
  SELECT
    *
  FROM
    CTE_seq_date_ranges
  WHERE
    timestep_idx < {labels_size}),
  # Join timescale information with data to be aggregated over timescale
  CTE_timescale_joined_data AS (
  SELECT
    timescale_idx,
    unix_timescale_start_date,
    unix_timescale_end_date,
    all_sales.sale_price
  FROM
    `{project}.{dataset}.{date_range_table}` AS start_end_timescale_date_range
  INNER JOIN
    `{project}.{sales_dataset_table}` AS all_sales
  ON
    start_end_timescale_date_range.unix_timescale_start_date <= UNIX_DATE(CAST(all_sales.sale_date AS DATE))
    AND UNIX_DATE(CAST(all_sales.sale_date AS DATE)) <= start_end_timescale_date_range.unix_timescale_end_date),
  # Group data we want aggregated over timescale
  CTE_grouped_data AS (
  SELECT
    timescale_idx,
    unix_timescale_start_date,
    unix_timescale_end_date,
    APPROX_QUANTILES(sale_price, 100)[
  OFFSET
    (50)] AS {value_name}
  FROM
    CTE_timescale_joined_data
  GROUP BY
    timescale_idx,
    unix_timescale_start_date,
    unix_timescale_end_date),
  # Join features data to features date ranges
  CTE_features AS (
  SELECT
    A.seq_idx,
    A.timestep_idx,
    A.seq_unix_start_date,
    IFNULL(B.{value_name},
      0) AS {value_name}
  FROM
    CTE_seq_features_date_range AS A
  INNER JOIN
    CTE_grouped_data AS B
  ON
    A.timescale_idx = B.timescale_idx),
  # Aggregate features data into sequences
  CTE_seq_features AS (
  SELECT
    seq_idx,
    seq_unix_start_date,
    STRING_AGG(CAST({value_name} AS STRING), ';'
    ORDER BY
      timestep_idx) AS {value_name}_agg
  FROM
    CTE_features
  GROUP BY
    seq_idx,
    seq_unix_start_date),
  # Join labels data to labels date ranges
  CTE_labels AS (
  SELECT
    A.seq_idx,
    A.timestep_idx,
    A.seq_unix_start_date,
    IFNULL(B.{value_name},
      0) AS {value_name}
  FROM
    CTE_seq_labels_date_range AS A
  INNER JOIN
    CTE_grouped_data AS B
  ON
    A.timescale_idx = B.timescale_idx),
  # Aggregate labels data into sequences
  CTE_seq_labels AS (
  SELECT
    seq_idx,
    seq_unix_start_date,
    STRING_AGG(CAST({value_name} AS STRING), ';'
    ORDER BY
      timestep_idx) AS labels_agg
  FROM
    CTE_labels
  GROUP BY
    seq_idx,
    seq_unix_start_date)
  # Join features with labels with horizon in between
  SELECT
    DATE_FROM_UNIX_DATE(A.seq_unix_start_date) AS feat_seq_start_date,
    DATE_FROM_UNIX_DATE(A.seq_unix_start_date + {window_size} * {downsample_size} - 1) AS feat_seq_end_date,
    DATE_FROM_UNIX_DATE(B.seq_unix_start_date) AS lab_seq_start_date,
    DATE_FROM_UNIX_DATE(B.seq_unix_start_date + {labels_size} * {downsample_size} - 1) AS lab_seq_end_date,
    {value_name}_agg,
    labels_agg
  FROM
    CTE_seq_features AS A
  INNER JOIN
    CTE_seq_labels AS B
  ON
    A.seq_unix_start_date + ({window_size} * {downsample_size} - 1) + ({downsample_size} * {horizon}) = B.seq_unix_start_date
  ORDER BY
    A.seq_idx
    """.format(project=project,
               dataset=dataset,
               date_range_table=date_range_table,
               sales_dataset_table=sales_dataset_table,
               value_name=value_name,
               downsample_size=downsample_size,
               window_size=window_size,
               horizon=horizon,
               labels_size=labels_size)
    
    return sql_csv_sub_sequences