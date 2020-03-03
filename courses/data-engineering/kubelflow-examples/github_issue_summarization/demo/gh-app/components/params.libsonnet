{
  global: {},
  components: {
    // Component-level parameters, defined initially from 'ks prototype use ...'
    // Each object below should correspond to a component in the components/ directory
    "issue-summarization": {
      endpoint: "REST",
      image: "gcr.io/kubeflow-images-public/issue-summarization:0.1",
      name: "issue-summarization",
      namespace: "kubeflow",
      pvcName: "github-issues-data",
      replicas: 1,
      imagePullSecret: "null",
    },
    "issue-summarization-ui": {
      containerPort: 80,
      image: "gcr.io/kubeflow-images-public/issue-summarization-ui:latest",
      name: "issue-summarization-ui",
      namespace: "kubeflow",
      replicas: 1,
      servicePort: 80,
      // Need node port to expose it via ingress.
      type: "NodePort",
    },
  },
}
