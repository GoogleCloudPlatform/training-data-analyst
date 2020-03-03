{
  global: {
    // User-defined global parameters; accessible to all component and environments, Ex:
    // replicas: 4,
  },
  components: {
    // Component-level parameters, defined initially from 'ks prototype use ...'
    // Each object below should correspond to a component in the components/ directory
    code_search: {
      bucket: "kubeflow-ci_temp",
      name: "kubeflow-code_search",
      namespace: "kubeflow-test-infra",
      prow_env: "BUILD_NUMBER=997a,BUILD_ID=997a,JOB_NAME=kubeflow-examples-presubmit-test,JOB_TYPE=presubmit,PULL_NUMBER=374,REPO_NAME=examples,REPO_OWNER=kubeflow",
    },
    gis: {
      bucket: "kubeflow-ci_temp",
      name: "kubeflow-gis",
      namespace: "kubeflow-test-infra",
      prow_env: "BUILD_NUMBER=997a,BUILD_ID=997a,JOB_NAME=kubeflow-examples-presubmit-test,JOB_TYPE=presubmit,PULL_NUMBER=374,REPO_NAME=examples,REPO_OWNER=kubeflow",
    },
    mnist: {
      bucket: "kubeflow-ci_temp",
      name: "kubeflow-mnist",
      namespace: "kubeflow-test-infra",
      prow_env: "BUILD_NUMBER=997a,BUILD_ID=997a,JOB_NAME=kubeflow-examples-presubmit-test,JOB_TYPE=presubmit,PULL_NUMBER=374,REPO_NAME=examples,REPO_OWNER=kubeflow",
    },
    xgboost_ames_housing: {
      bucket: "kubeflow-ci_temp",
      name: "kubeflow-xgboost-ames-housing",
      namespace: "kubeflow-test-infra",
      prow_env: "BUILD_NUMBER=997a,BUILD_ID=997a,JOB_NAME=kubeflow-examples-presubmit-test,JOB_TYPE=presubmit,PULL_NUMBER=374,REPO_NAME=examples,REPO_OWNER=kubeflow",
    },
    pytorch_mnist: {
          bucket: "kubeflow-ci_temp",
          name: "kubeflow-pytorch_mnist",
          namespace: "kubeflow-test-infra",
          prow_env: "BUILD_NUMBER=997a,BUILD_ID=997a,JOB_NAME=kubeflow-examples-presubmit-test,JOB_TYPE=presubmit,PULL_NUMBER=374,REPO_NAME=examples,REPO_OWNER=kubeflow",
        },
    xgboost_synthetic: {
      bucket: "kubeflow-ci_temp",
      name: "kubeflow-xgboost_synthetic",
      namespace: "kubeflow-test-infra",
      prow_env: "BUILD_NUMBER=997a,BUILD_ID=997a,JOB_NAME=kubeflow-examples-presubmit-test,JOB_TYPE=presubmit,PULL_NUMBER=374,REPO_NAME=examples,REPO_OWNER=kubeflow",
    },
    workflows: {
      bucket: "kubeflow-ci_temp",
      name: "kubeflow-examples-presubmit-test-374-6e32",
      namespace: "kubeflow-test-infra",
      prow_env: "BUILD_NUMBER=997a,BUILD_ID=997a,JOB_NAME=kubeflow-examples-presubmit-test,JOB_TYPE=presubmit,PULL_NUMBER=374,REPO_NAME=examples,REPO_OWNER=kubeflow",
    },
  },
}
