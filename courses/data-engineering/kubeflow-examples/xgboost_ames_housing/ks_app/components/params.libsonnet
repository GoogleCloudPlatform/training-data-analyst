{
  global: {},
  components: {
    // Component-level parameters, defined initially from 'ks prototype use ...'
    // Each object below should correspond to a component in the components/ directory
    seldon: {
      apifeServiceType: "NodePort",
      grpcMaxMessageSize: "4194304",
      name: "seldon",
      operatorJavaOpts: "null",
      operatorSpringOpts: "null",
      seldonVersion: "0.2.3",
      withAmbassador: "false",
      withApife: "false",
      withRbac: "true",
    },
    "xgboost": {
      endpoint: "REST",
      image: "image-path",
      imagePullSecret: "null",
      name: "xgboost",
      pvcName: "null",
      replicas: 1,
    },
  },
}
