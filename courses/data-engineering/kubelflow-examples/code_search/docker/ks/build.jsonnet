// TODO(jlewi): We should tag the image latest and then
// use latest as a cache so that rebuilds are fast
// https://cloud.google.com/cloud-build/docs/speeding-up-builds#using_a_cached_docker_image
{
	
	"steps": [      
    {
      "id": "build",
      "name": "gcr.io/cloud-builders/docker",
      "args": ["build", "-t", "gcr.io/kubeflow-examples/code-search/ks:" + std.extVar("tag"),
             	 "--label=git-versions=" + std.extVar("gitVersion"),
               "--file=docker/ks/Dockerfile",
               "."],
    },
    {
      "id": "tag",
      "name": "gcr.io/cloud-builders/docker",
      "args": ["tag", "gcr.io/kubeflow-examples/code-search/ks:" + std.extVar("tag"),
               "gcr.io/kubeflow-examples/code-search/ks:latest",],
      "waitFor": ["build"],
    },
  ],
  "images": ["gcr.io/kubeflow-examples/code-search/ks:" + std.extVar("tag"),
             "gcr.io/kubeflow-examples/code-search/ks:latest",
            ],
}