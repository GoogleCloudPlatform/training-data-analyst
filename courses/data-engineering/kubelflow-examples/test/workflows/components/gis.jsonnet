// Test workflow for GitHub Issue Summarization.
//
local env = std.extVar("__ksonnet/environments");
local overrides = std.extVar("__ksonnet/params").components.gis;

local k = import "k.libsonnet";
local util = import "util.libsonnet";

// Define default params and then combine them with any overrides
local defaultParams = {
  // local nfsVolumeClaim: "kubeflow-testing",
  nfsVolumeClaim: "nfs-external",

  // The name to use for the volume to use to contain test data.
  dataVolume: "kubeflow-test-volume",

  // Default step image:
  stepImage: "gcr.io/kubeflow-ci/test-worker:v20190104-f2a1cdf-e3b0c4",

  // Which Kubeflow cluster to use for running TFJobs on.
  kfProject: "kubeflow-ci",
  kfZone: "us-east1-b",
  kfCluster: "kf-vmaster-n00",
};

local params = defaultParams + overrides;

local prowEnv = util.parseEnv(params.prow_env);

// Workflow template is the name of the workflow template; typically the name of the ks component.
// This is used as a label to make it easy to identify all Argo workflows created from a given
// template.
local workflow_template = "gis";

// Create a dictionary of the different prow variables so we can refer to them in the workflow.
//
// Important: We want to initialize all variables we reference to some value. If we don't
// and we reference a variable which doesn't get set then we get very hard to debug failure messages.
// In particular, we've seen problems where if we add a new environment and evaluate one component eg. "workflows"
// and another component e.g "code_search.jsonnet" doesn't have a default value for BUILD_ID then ksonnet
// fails because BUILD_ID is undefined.
local prowDict = {
	BUILD_ID: "notset",
	BUILD_NUMBER: "notset",
	REPO_OWNER: "notset",
	REPO_NAME: "notset",
	JOB_NAME: "notset",
	JOB_TYPE: "notset",
	PULL_NUMBER: "notset",
 } + util.listOfDictToMap(prowEnv);

local bucket = params.bucket;

// mountPath is the directory where the volume to store the test data
// should be mounted.
local mountPath = "/mnt/" + "test-data-volume";
// testDir is the root directory for all data for a particular test run.
local testDir = mountPath + "/" + params.name;
// outputDir is the directory to sync to GCS to contain the output for this job.
local outputDir = testDir + "/output";
local artifactsDir = outputDir + "/artifacts";

// Source directory where all repos should be checked out
local srcRootDir = testDir + "/src";

// The directory containing the kubeflow/kubeflow repo
local srcDir = srcRootDir + "/" + prowDict.REPO_OWNER + "/" + prowDict.REPO_NAME;

// value of KUBECONFIG environment variable. This should be  a full path.
local kubeConfig = testDir + "/.kube/kubeconfig";

// The directory within the kubeflow_testing and kubeflow_tf-operator submodule containing
// py scripts to use.
local kubeflowTestingPy = srcRootDir + "/kubeflow/testing/py";

local tfOperatorPy = srcRootDir + "/kubeflow/tf-operator/py";



// These variables control where the docker images get pushed and what
// tag to use
local imageBase = "gcr.io/kubeflow-ci/github-issue-summarization";
local imageTag = "build-" + prowDict["BUILD_ID"];
local trainerImage = imageBase + "/trainer-estimator:" + imageTag;

// Build template is a template for constructing Argo step templates.
//
// step_name: Name for the template
// command: List to pass as the container command.
//
// We customize the defaults for each step in the workflow by modifying
// buildTemplate.argoTemplate
local buildTemplate = {
  // name & command variables should be overwritten for every test.
  // Other variables can be changed per step as needed.
  // They are hidden because they shouldn't be included in the Argo template
  name: "",
  command:: "",
  image: params.stepImage,
  workingDir:: null,
  env_vars:: [],
  side_cars: [],
  pythonPath: kubeflowTestingPy + ":" + tfOperatorPy,


  activeDeadlineSeconds: 1800,  // Set 30 minute timeout for each template

  local template = self,


  // Actual template for Argo
  argoTemplate: {
    name: template.name,
    metadata: {
      labels: prowDict + {
        workflow: params.name,
        workflow_template: workflow_template,
        step_name: + template.name,
      },
    },
    container: {
      command: template.command,
      name: template.name,
      image: template.image,
      workingDir: template.workingDir,
      env: [
        {
          // Add the source directories to the python path.
          name: "PYTHONPATH",
          value: template.pythonPath,
        },
        {
          name: "GOOGLE_APPLICATION_CREDENTIALS",
          value: "/secret/gcp-credentials/key.json",
        },
        {
          name: "GITHUB_TOKEN",
          valueFrom: {
            secretKeyRef: {
              name: "github-token",
              key: "github_token",
            },
          },
        },
        {
          // We use a directory in our NFS share to store our kube config.
          // This way we can configure it on a single step and reuse it on subsequent steps.
          name: "KUBECONFIG",
          value: kubeConfig,
        },
      ] + prowEnv + template.env_vars,
      volumeMounts: [
        {
          name: params.dataVolume,
          mountPath: mountPath,
        },
        {
          name: "github-token",
          mountPath: "/secret/github-token",
        },
        {
          name: "gcp-credentials",
          mountPath: "/secret/gcp-credentials",
        },
      ],
    },
  },
};  // buildTemplate

// Create a list of dictionary.
// Each item is a dictionary describing one step in the graph.
local dagTemplates = [
  {
    template: buildTemplate {
      name: "checkout",
      command:
        ["/usr/local/bin/checkout.sh", srcRootDir],

      env_vars: [{
        name: "EXTRA_REPOS",
        // tf-operator has utilities needed for testing TFJobs.
        // TODO(jlewi): Update extra repos once kubeflow/testing#271 are merged.
        value: "kubeflow/testing@HEAD:274;kubeflow/tf-operator@HEAD",
      }],
    },
    dependencies: null,
  },  // checkout
  {
    // TODO(https://github.com/kubeflow/testing/issues/257): Create-pr-symlink
    // should be done by run_e2e_workflow.py
    template: buildTemplate {
      name: "create-pr-symlink",
      command: [
        "python",
        "-m",
        "kubeflow.testing.prow_artifacts",
        "--artifacts_dir=" + outputDir,
        "create_pr_symlink",
        "--bucket=" + params.bucket,
      ],
    },  // create-pr-symlink
    dependencies: ["checkout"],
  },  // create-pr-symlink
  {
    // Submit a GCB job to build the images
    template: buildTemplate {
      name: "build-images",
      command: util.buildCommand([
      [
        "gcloud",
        "auth",
        "activate-service-account",
        "--key-file=${GOOGLE_APPLICATION_CREDENTIALS}",
      ],
      	[
        "make",
        "build-gcb",
        "IMG=" + imageBase,
        "TAG=" + imageTag,
      ]]
      ),
      workingDir: srcDir + "/github_issue_summarization",
    },
    dependencies: ["checkout"],
  }, // build-images
  {
    // Run the python test to train the model
    template: buildTemplate {
      name: "train-test",
      command: [
        "python",
        "train_test.py",
      ],
      // Use the newly built image.
      image: trainerImage,
      workingDir: "/issues",
    },
    dependencies: ["build-images"],
  },  // train-test
  {
    // Configure KUBECONFIG
    template: buildTemplate {
      name: "get-kubeconfig",
      command: util.buildCommand([
      [
        "gcloud",
        "auth",
        "activate-service-account",
        "--key-file=${GOOGLE_APPLICATION_CREDENTIALS}",
      ],
      [
        "gcloud",
        "--project=" + params.kfProject,
        "container",
        "clusters",
        "get-credentials",
        "--zone=" + params.kfZone,
        params.kfCluster,
      ]]
      ),
      workingDir: srcDir + "/github_issue_summarization",
    },
    dependencies: ["checkout"],
  }, // get-kubeconfig
  {
    // Run the python test for TFJob
    template: buildTemplate {
      name: "tfjob-test",
      command: [
        "python",
        "tfjob_test.py",
        "--params=name=gis-test-" + prowDict["BUILD_ID"] + ",namespace=kubeflow,num_epochs=1,sample_size=10,image=" + trainerImage,
        "--artifacts_path=" + artifactsDir,
      ],
      workingDir: srcDir + "/github_issue_summarization/testing",
      pythonPath: tfOperatorPy + ":" + kubeflowTestingPy,
    },
    dependencies: ["build-images", "get-kubeconfig"],
  },  // tfjob-test
];

// Dag defines the tasks in the graph
local dag = {
  name: "e2e",
  // Construct tasks from the templates
  // we will give the steps the same name as the template
  dag: {
    tasks: util.toArgoTaskList(dagTemplates),
  },
};  // dag

// Define templates for the steps to be performed when the
// test exits
local exitTemplates =
  [
    {
      // Copy artifacts to GCS for gubernator.
      // TODO(https://github.com/kubeflow/testing/issues/257): Create-pr-symlink
      // should be done by run_e2e_workflow.py
      template: buildTemplate {
        name: "copy-artifacts",
        command: [
          "python",
          "-m",
          "kubeflow.testing.prow_artifacts",
          "--artifacts_dir=" + outputDir,
          "copy_artifacts",
          "--bucket=" + bucket,
        ],
      },  // copy-artifacts,

    },
    {
      // Delete the test directory in NFS.
      // TODO(https://github.com/kubeflow/testing/issues/256): Use an external process to do this.
      template:
        buildTemplate {
          name: "test-dir-delete",
          command: [
            "rm",
            "-rf",
            testDir,
          ],

          argoTemplate+: {
        	  retryStrategy: {
        	  	limit: 3,
        	  },
          },
        },  // test-dir-delete
      dependencies: ["copy-artifacts"],
    },
  ];

// Create a DAG representing the set of steps to execute on exit
local exitDag = {
  name: "exit-handler",
  // Construct tasks from the templates
  // we will give the steps the same name as the template
  dag: {
    tasks: util.toArgoTaskList(exitTemplates),
  },
};

// A list of templates for the actual steps
local stepTemplates = std.map(function(i) i.template.argoTemplate
                              , dagTemplates) +
                      std.map(function(i) i.template.argoTemplate
                              , exitTemplates);

// Define the Argo Workflow.
local workflow = {
  apiVersion: "argoproj.io/v1alpha1",
  kind: "Workflow",
  metadata: {
    name: params.name,
    namespace: env.namespace,
    labels: prowDict + {
      workflow_template: workflow_template,
    },
  },
  spec: {
    entrypoint: "e2e",
    volumes: [
      {
        name: "github-token",
        secret: {
          secretName: "github-token",
        },
      },
      {
        name: "gcp-credentials",
        secret: {
          secretName: "kubeflow-testing-credentials",
        },
      },
      {
        name: params.dataVolume,
        persistentVolumeClaim: {
          claimName: params.nfsVolumeClaim,
        },
      },
    ],  // volumes

    // onExit specifies the template that should always run when the workflow completes.
    onExit: "exit-handler",

    // The templates will be a combination of the templates
    // defining the dags executed by Argo as well as the templates
    // for the individual steps.
    templates: [dag, exitDag] + stepTemplates,  // templates
  },  // spec
};  // workflow

std.prune(k.core.v1.list.new([workflow]))
