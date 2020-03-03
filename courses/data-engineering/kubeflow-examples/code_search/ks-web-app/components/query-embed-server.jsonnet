local env = std.extVar("__ksonnet/environments");

local params = std.extVar("__ksonnet/params").components["query-embed-server"];
local k = import "k.libsonnet";

local deployment = k.apps.v1beta1.deployment;
local container = deployment.mixin.spec.template.spec.containersType;

local util = import "kubeflow/tf-serving/util.libsonnet";
local tfserving = import "kubeflow/tf-serving/tf-serving-template.libsonnet";

local base = tfserving.new(env, params);
local tfDeployment = base.tfDeployment +
                     deployment.mixin.spec.template.spec.withVolumesMixin(
                       if params.gcpCredentialSecretName != "null" then (
                         [{
                           name: "gcp-credentials",
                           secret: {
                             secretName: params.gcpCredentialSecretName,
                           },
                         }]
                       ) else [],
                     )+
                     deployment.mapContainers(
                       function(c) {
                         result::
                           c + container.withEnvMixin(
                             if params.gcpCredentialSecretName != "null" then (
                               [{
                                 name: "GOOGLE_APPLICATION_CREDENTIALS",
                                 value: "/secret/gcp-credentials/key.json",
                               }]
                             ) else [],
                           ) +
                           container.withVolumeMountsMixin(
                             if params.gcpCredentialSecretName != "null" then (
                               [{
                                 name: "gcp-credentials",
                                 mountPath: "/secret/gcp-credentials",
                               }]
                             ) else [],
                           ),
                       }.result,
                     );
util.list([
  tfDeployment,
  base.tfService,
],)
