// TODO(jlewi): We should tag the image latest and then
// use latest as a cache so that rebuilds are fast
// https://cloud.google.com/cloud-build/docs/speeding-up-builds#using_a_cached_docker_image
{

  // Convert non-boolean types like string,number to a boolean.
  // This is primarily intended for dealing with parameters that should be booleans.
  local toBool = function(x) {
    result::
      if std.type(x) == "boolean" then
        x
      else if std.type(x) == "string" then
        std.asciiUpper(x) == "TRUE"
      else if std.type(x) == "number" then
        x != 0
      else
        false,
  }.result,

  local useImageCache = toBool(std.extVar("useImageCache")),

  // A tempalte for defining the steps for building each image.
  //
  // TODO(jlewi): This logic is reused across a lot of examples; can we put in a shared
  // location and just import it?
  local subGraphTemplate = {
    // following variables must be set
    name: null,
    seldon: false,
    dockerFile: null,
    buildArg: null,
    contextDir: ".",

    local template = self,

    local rootDir = "/workspace/",

    local pullStep = if useImageCache then [
      {
        id: "pull-" + template.name,
        name: "gcr.io/cloud-builders/docker",
        args: ["pull", std.extVar("imageBase") + "/" + template.name + ":latest"],
        waitFor: ["-"],
      },
    ] else [],

    local image = std.extVar("imageBase") + "/" + template.name + ":" + std.extVar("tag"),
    local imageLatest = std.extVar("imageBase") + "/" + template.name + ":latest",

    images: [image, imageLatest],
    steps: pullStep + if template.seldon then
           [
             {
               id: "wrap-" + template.name,
               name: "gcr.io/cloud-builders/docker",
               args: [
                       "run",
                       "-v",
                       rootDir + template.contextDir + ":/my_model",
                       "seldonio/core-python-wrapper:0.7",
                       "/my_model",
                       "mnistddpserving",
                       std.extVar("tag"),
                       std.extVar("imageBase"),
                       "--grpc",
                       "--force"
                     ],
               waitFor: if useImageCache then ["pull-" + template.name] else ["-"],
             },
             {
               id: "build-" + template.name,
               name: "gcr.io/cloud-builders/docker",
               args: [
                       "build",
                       "-t",
                       image,
                       rootDir + template.contextDir + "/build"
                     ],
               waitFor: ["wrap-" + template.name],
             },
             {
               id: "tag-" + template.name,
               name: "gcr.io/cloud-builders/docker",
               args: ["tag", image, imageLatest],
               waitFor: ["build-" + template.name],
             },
           ]
           else
           [
             {
               local buildArgList = if template.buildArg != null then ["--build-arg", template.buildArg] else [],
               local cacheList = if useImageCache then ["--cache-from=" + imageLatest] else [],

               id: "build-" + template.name,
               name: "gcr.io/cloud-builders/docker",
               args: [
                       "build",
                       "-t",
                       image,
                       "--label=git-versions=" + std.extVar("gitVersion"),
                     ]
                     + buildArgList
                     + [
                       "--file=" + template.dockerFile,
                     ]
                     + cacheList + [template.contextDir],
               waitFor: if useImageCache then ["pull-" + template.name] else ["-"],
             },
             {
               id: "tag-" + template.name,
               name: "gcr.io/cloud-builders/docker",
               args: ["tag", image, imageLatest],
               waitFor: ["build-" + template.name],
             },
           ],
  },

  local trainCPUSteps = subGraphTemplate {
      name: "traincpu",
      dockerFile: "./training/ddp/mnist/Dockerfile.traincpu",
      contextDir: "./training/ddp/mnist"
    },

  local trainGPUSteps = subGraphTemplate {
        name: "traingpu",
        dockerFile: "./training/ddp/mnist/Dockerfile.traingpu",
        contextDir: "./training/ddp/mnist"
      },

  local servingSteps = subGraphTemplate {
    name: "serving",
    seldon: true,
    contextDir: "/serving/seldon-wrapper"
  },

  local ksonnetSteps = subGraphTemplate {
    name: "ksonnet",
    dockerFile: "./Dockerfile.ksonnet",
    contextDir: "."
  },

  local uiSteps = subGraphTemplate {
    name: "web-ui",
    dockerFile: "./web-ui/Dockerfile",
    contextDir: "./web-ui"
  },

  steps: trainCPUSteps.steps + trainGPUSteps.steps + servingSteps.steps + ksonnetSteps.steps + uiSteps.steps,
  images: trainCPUSteps.images + trainGPUSteps.images + servingSteps.images + ksonnetSteps.images + uiSteps.images,
}
