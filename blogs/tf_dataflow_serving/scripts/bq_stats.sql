#standardsql

SELECT
  DATETIME_DIFF(datetime(MAX(predict_timestamp)), datetime(MIN(source_timestamp)), MINUTE) total_time_min,
  ROUND(AVG(DATETIME_DIFF(datetime(predict_timestamp), datetime(source_timestamp), SECOND)),2) avg_latency_time_sec,
  COUNT(*) instance_count
FROM
  `ksalama-gcp-playground.playground_ds.babyweight_estimates`