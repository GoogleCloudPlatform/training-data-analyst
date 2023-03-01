project_name: "looker_blocks_qwiklab"

constant: CONNECTION_NAME {
  value: "bigquery_public_data_looker"
}

remote_dependency: weather {
  url: "https://github.com/meghabedi/training-data-analyst/tree/looker-block-lab/self-paced-labs/looker-block/block-weather"
  ref: "master"
  override_constant: CONNECTION_NAME {
    value: "@{CONNECTION_NAME}"
  }
}
