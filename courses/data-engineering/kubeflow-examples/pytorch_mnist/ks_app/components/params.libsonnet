{
  global: {
    // User-defined global parameters; accessible to all component and environments, Ex:
    // replicas: 4,
  },
  components: {
    // Component-level parameters, defined initially from 'ks prototype use ...'
    // Each object below should correspond to a component in the components/ directory
    "web-ui": {
      containerPort: 5000,
      image: "gcr.io/kubeflow-examples/pytorch-mnist/web-ui",
      name: "web-ui",
      replicas: 1,
      servicePort: 80,
      type: "ClusterIP",
    },
    serving_model: {
        image: "gcr.io/kubeflow-examples/pytorch-mnist/serving",
        name : "mnist-classifier",
        mountPath: "/mnt/kubeflow-gcfs",
        replicas: 1,
        endpointType: "GRPC",
        modelName: "pytorch-model",
        modelType: "MODEL"
    },
  },
}
