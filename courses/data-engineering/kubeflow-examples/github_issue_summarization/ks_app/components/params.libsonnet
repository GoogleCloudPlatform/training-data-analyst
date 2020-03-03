{
  global: {},
  components: {
    // Component-level parameters, defined initially from 'ks prototype use ...'
    // Each object below should correspond to a component in the components/ directory
    "data-downloader": {},
    "data-pvc": {},
    "hp-tune": {},
    "issue-summarization-model": {
      endpoint: "REST",
      image: "gcr.io/kubeflow-examples/issue-summarization-model:v20180427-e2aa113",
      name: "issue-summarization",
      namespace: "null",
      replicas: 2,
    },
    "tensor2tensor": {
      name: "tensor2tensor",
    },
    tensorboard: {
      image: "tensorflow/tensorflow:1.7.0",
      // logDir needs to be overwritten based on where the data is
      // actually stored.
      logDir: "",
      name: "gh",
    },
    "tfjob": {
      name: "tfjob-issue-summarization",
      image: "gcr.io/kubeflow-examples/github-issue-summarization/trainer-estimator:v20181229-v0.2-131-g662c666-dirty-312900",
      input_data: "gs://kubeflow-examples/github-issue-summarization-data/github_issues_sample.csv",
      output_model: "/tmp/model.h5",
      sample_size: "100000",
      num_epochs: "7",
      gcpSecretName: "user-gcp-sa",
      gcpSecretFile: "user-gcp-sa.json",
    },
    "tfjob-pvc": {
      name: "tfjob-pvc",
    },
    ui: {
      namespace: "null",
      githubToken: "",
      image: "gcr.io/kubeflow-examples/issue-summarization-ui:v20180629-v0.1-2-g98ed4b4-dirty-182929",
    },
    // Run tensorboard with pvc.
    // This is intended for use with tfjob-estimator
  },
}
