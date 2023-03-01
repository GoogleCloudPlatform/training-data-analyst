project_name: "looker_blocks_qwiklab"

constant: CONNECTION_NAME {
  value: "bigquery_public_data_looker"
}

remote_dependency: weather {
  url: "https://github.com/looker-open-source/block-weather"
  ref: "d9b54da9cac9946b6b23ef4c4bb1de965a7313ca"
  override_constant: CONNECTION_NAME {
    value: "@{CONNECTION_NAME}"
  }
}
