{
  global: {
    // User-defined global parameters; accessible to all component and environments, Ex:
    // replicas: 4,
  },
  components: {
    // Component-level parameters, defined initially from 'ks prototype use ...'
    // Each object below should correspond to a component in the components/ directory
    "kubeflow-core": {
      cloud: "null",
      disks: "null",
      jupyterHubAuthenticator: "null",
      jupyterHubImage: "gcr.io/kubeflow/jupyterhub-k8s:1.0.1",
      jupyterHubServiceType: "ClusterIP",
      name: "kubeflow-core",
      namespace: "poetry",
      tfDefaultImage: "null",
      tfJobImage: "gcr.io/tf-on-k8s-dogfood/tf_operator:v20180131-cabc1c0-dirty-e3b0c44",
      tfJobUiServiceType: "ClusterIP",
    },
    servePoetry: {
      http_proxy_image: "gcr.io/kubeflow/http-proxy:1.0",
      model_path: "gs://cloud-training-demos-ml/poetry/model_full/export/poetry/",
      model_server_image: "gcr.io/kubeflow/model-server:1.0",
      name: "poetry",
      namespace: "poetry",
      ipName: "mlpoetry-ingress",
    },
  },
}
