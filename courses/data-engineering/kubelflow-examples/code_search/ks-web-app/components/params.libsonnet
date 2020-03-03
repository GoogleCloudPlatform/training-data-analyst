{
  global: {
    // User-defined global parameters; accessible to all component and environments, Ex:
    // replicas: 4,
    problem: "kf_github_function_docstring",
  },
  components: {
    // Component-level parameters, defined initially from 'ks prototype use ...'
    // Each object below should correspond to a component in the components/ directory

	  // search-index-server provides the web app and nsmlib index.
	  "search-index-server": {
		name: "search-index-server",			
		// 1 replica is convenient for debugging but we should bump after debugging.
		replicas: 1,
		image: "gcr.io/kubeflow-examples/code-search-ui:v20181122-dc0e646-dirty-043a63",

		// Parameters that are unique to each deployment.
		lookupFile: null,
		indexFile: null,
		servingUrl: "http://query-embed-server.kubeflow:8500/v1/models/t2t-code-search:predict",
		dataDir: null,
	  },

	  // TFServing instance that embeds code.
	  "query-embed-server": {
	      name: "query-embed-server",
	      gcpCredentialSecretName: "user-gcp-sa",
	      serviceType: "ClusterIP",
	      deployHttpProxy: false,	      
	      // modelName is used by the client.
	      modelName: "t2t-code-search",
	      defaultCpuImage: "tensorflow/serving:1.11.1",
	      defaultGpuImage: "tensorflow/serving:1.11.1-gpu",
	      httpProxyImage: "gcr.io/kubeflow-images-public/tf-model-server-http-proxy:v20180723",
	      numGpus: "0",

	      // Parameters that are unique to each path
	      modelBasePath: null,
	    },
  },
}
