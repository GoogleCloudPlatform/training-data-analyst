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
  local subGraphTemplate = {
    // following variables must be set
    name: null,

    dockerFile: null,
    buildArg: null,

    local template = self,

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
    steps: pullStep +
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
                     + cacheList + ["."],
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

  local cpuSteps = subGraphTemplate {
    name: "t2t-cpu",
    dockerFile: "docker/t2t/Dockerfile",
    baseImageTag: "BASE_IMAGE_TAG=1.11.0",
  },

  local gpuSteps = subGraphTemplate {
    name: "t2t-gpu",
    dockerFile: "docker/t2t/Dockerfile",
    baseImageTag: "BASE_IMAGE_TAG=1.11.0-gpu",
  },

  local dataflowSteps = subGraphTemplate {
    name: "dataflow",
    dockerFile: "docker/t2t/Dockerfile.dataflow",
  },

  steps: cpuSteps.steps + gpuSteps.steps + dataflowSteps.steps,
  images: cpuSteps.images + gpuSteps.images + dataflowSteps.images,
}
