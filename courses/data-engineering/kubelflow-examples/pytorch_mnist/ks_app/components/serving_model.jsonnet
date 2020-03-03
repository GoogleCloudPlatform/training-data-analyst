local env = std.extVar("__ksonnet/environments");
local params = std.extVar("__ksonnet/params").components["serving_model"];
[
    {
      "apiVersion": "machinelearning.seldon.io/v1alpha2",
      "kind": "SeldonDeployment",
      "metadata": {
        "labels": {
          "app": "seldon"
        },
        "name": params.name
      },
      "spec": {
        "annotations": {
          "deployment_version": "v1",
          "project_name": "MNIST Example"
        },
        "name": params.name,
        "predictors": [
          {
            "annotations": {
              "predictor_version": "v1"
            },
            "componentSpecs": [{
              "spec": {
                "containers": [
                  {
                    "image": params.image,
                    "imagePullPolicy": "Always",
                    "name": "pytorch-model",
                    "volumeMounts": [
                      {
                        "mountPath": params.mountPath,
                        "name": "persistent-storage"
                      }
                    ]
                  }
                ],
                "terminationGracePeriodSeconds": 1,
                "volumes": [
                  {
                    "name": "persistent-storage",
                    "volumeSource" : {
                      "persistentVolumeClaim": {
                        "claimName": "kubeflow-gcfs"
                      }
                    }
                  }
                ]
              }
            }],
            "graph": {
              "children": [],
              "endpoint": {
                "type": params.endpointType
              },
              "name": params.modelName,
              "type": params.modelType
            },
            "name": "mnist-ddp-serving",
            "replicas": params.replicas
          }
        ]
      }
    }
]