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
    contextDir: ".",

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

  local uiSteps = subGraphTemplate {
    name: "ui",
    dockerFile: "./docker/Dockerfile",
    contextDir: "./docker"
  },

  local trainerSteps = subGraphTemplate {
    name: "trainer",
    dockerFile: "./notebooks/Dockerfile",
    contextDir: "./notebooks"
  },

  local trainerEstimatorSteps = subGraphTemplate {
    name: "trainer-estimator",
    dockerFile: "./notebooks/Dockerfile.estimator",
    contextDir: "./notebooks"
  },

  steps: uiSteps.steps + trainerSteps.steps + trainerEstimatorSteps.steps,
  images: uiSteps.images + trainerSteps.images + trainerEstimatorSteps.images,
}
