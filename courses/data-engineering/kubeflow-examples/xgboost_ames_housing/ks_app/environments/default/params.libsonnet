local params = std.extVar('__ksonnet/params');
local globals = import 'globals.libsonnet';
local envParams = params + {
  components+: {
    xgboost+: {
      name: 'xgboost-ames-1300',
      image: 'gcr.io/kubeflow-ci/xgboost_ames_housing:build-1300',
      replicas: 1,
    },
  },
};

{
  components: {
    [x]: envParams.components[x] + globals
    for x in std.objectFields(envParams.components)
  },
}