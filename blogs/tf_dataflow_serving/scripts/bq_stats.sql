#standardsql

SELECT
  DATETIME_DIFF(datetime(MAX(predict_timestamp)), datetime(MIN(source_timestamp)), SECOND) total_time_sec,
  ROUND(MIN(DATETIME_DIFF(datetime(predict_timestamp), datetime(source_timestamp), SECOND)),2) min_latency_time_sec,
  ROUND(MAX(DATETIME_DIFF(datetime(predict_timestamp), datetime(source_timestamp), SECOND)),2) max_latency_time_sec,
  ROUND(AVG(DATETIME_DIFF(datetime(predict_timestamp), datetime(source_timestamp), SECOND)),2) avg_latency_time_sec,
  COUNT(*) instance_count
FROM
  `ksalama-gcp-playground.playground_ds.babyweight_estimates`