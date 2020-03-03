local env = std.extVar("__ksonnet/environments");
local params = std.extVar("__ksonnet/params").components["google-cloud-filestore-pv"];

local google_cloud_file_store_pv = import "kubeflow/core/google-cloud-filestore-pv.libsonnet";
local instance = google_cloud_file_store_pv.new(env, params);
instance.list(instance.all)
