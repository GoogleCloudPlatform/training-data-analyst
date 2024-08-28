# Canary Deployments with Cloud Run and Cloud Build

This document shows you how to implement a deployment pipeline for
Cloud Run that implements progression of code from developer
branches to production with automated canary testing and percentage-based
traffic management. It is intended for platform administrators who are
responsible for creating and managing CI/CD pipelines to
GKE. This document assumes that you have a basic
understanding of Git, Cloud Run, and CI/CD pipeline concepts.

Cloud Run lets you deploy and run your applications with little
overhead or effort. Many organizations use robust release pipelines to move code
into production. Cloud Run provides unique traffic management
capabilities that let you implement advanced release management techniques with
little effort.

-   Create your Cloud Run service
-   Enable a developer branch
-   Implement canary testing
-   Roll out safely to production


## Preparing your environment

1.  In Cloud Shell, create environment variables to use throughout
    this tutorial:

    ```sh
    export PROJECT_ID=$(gcloud config get-value project)
    export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
    ```
2.  Enable the following APIs:

    - Resource Manager
    - GKE
    - Cloud Source Repositories
    - Cloud Build
    - Container Registry
    - Cloud Run

    ```sh
    gcloud services enable \
      cloudresourcemanager.googleapis.com \
      container.googleapis.com \
      sourcerepo.googleapis.com \
      cloudbuild.googleapis.com \
      containerregistry.googleapis.com \
      run.googleapis.com
    ```
3.  Grant the Cloud Run Admin role (`roles/run.admin`) to
    the Cloud Build service account:

    ```sh
    gcloud projects add-iam-policy-binding $PROJECT_ID \
      --member=serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com \
      --role=roles/run.admin
    ```
4.  Grant the IAM Service Account User role
    (`roles/iam.serviceAccountUser`) to the Cloud Build service
    account for the Cloud Run runtime service account:

    ```sh
    gcloud iam service-accounts add-iam-policy-binding \
      $PROJECT_NUMBER-compute@developer.gserviceaccount.com \
      --member=serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com \
      --role=roles/iam.serviceAccountUser
    ```
5.  If you haven't used Git in Cloud Shell previously, set the
    `user.name` and `user.email` values that you want to use:

    ```sh
    git config --global user.email "YOUR_EMAIL_ADDRESS"
    git config --global user.name "YOUR_USERNAME"
    ```
6.  Clone and prepare the sample repository:

    ```sh
    git clone https://github.com/GoogleCloudPlatform/software-delivery-workshop cloudrun-progression

    cd cloudrun-progression/labs/cloudrun-progression
    rm -rf ../../.git
    ```
7.  Replace placeholder values in the sample repository with your `PROJECT_ID`:

    ```sh
    sed "s/PROJECT/${PROJECT_ID}/g" branch-trigger.json-tmpl > branch-trigger.json
    sed "s/PROJECT/${PROJECT_ID}/g" master-trigger.json-tmpl > master-trigger.json
    sed "s/PROJECT/${PROJECT_ID}/g" tag-trigger.json-tmpl > tag-trigger.json
    ```
8.  Store the code from the sample repository in CSR:

    ```sh
    gcloud source repos create cloudrun-progression
    git init
    git config credential.helper gcloud.sh
    git remote add gcp https://source.developers.google.com/p/$PROJECT_ID/r/cloudrun-progression
    git branch -m master
    git add . && git commit -m "initial commit"
    git push gcp master
    ```

## Creating your Cloud Run service

In this section, you build and deploy the initial production application that
you use throughout this tutorial.

1.  In Cloud Shell, build and deploy the application, including a
    service that requires authentication. To make a public service, use the
    `--allow-unauthenticated` flag as described in
    [Allowing public (unauthenticated) access](/run/docs/authenticating/public).

    ```sh
    gcloud builds submit --tag gcr.io/$PROJECT_ID/hello-cloudrun
    gcloud run deploy hello-cloudrun \
      --image gcr.io/$PROJECT_ID/hello-cloudrun \
      --platform managed \
      --region us-central1 \
      --tag=prod -q
    ```

    The output looks like the following:

    ```none 
    Deploying container to Cloud Run service [hello-cloudrun] in project [sdw-mvp6] region [us-central1]
    ✓ Deploying new service... Done.
      ✓ Creating Revision...
      ✓ Routing traffic...
    Done.
    Service [hello-cloudrun] revision [hello-cloudrun-00001-tar] has been deployed and is serving 100 percent of traffic.
    Service URL: https://hello-cloudrun-apwaaxltma-uc.a.run.app
    The revision can be reached directly at https://prod---hello-cloudrun-apwaaxltma-uc.a.run.app
    ```

    The output includes the service URL and a unique URL for the revision. Your
    values will differ slightly from what's indicated here.
2.  After the deployment is complete, view the newly deployed service on
    the
    [Revisions page](https://console.cloud.google.com/run/detail/us-central1/hello-cloudrun/revisions)
    in the Console.

    [Go to Revisions](https://console.cloud.google.com/run/detail/us-central1/hello-cloudrun/revisions)

3.  In Cloud Shell, view the authenticated service response:

    ```sh
    PROD_URL=$(gcloud run services describe hello-cloudrun \
      --platform managed \
      --region us-central1 \
      --format=json | jq \
      --raw-output ".status.url")
    echo $PROD_URL
    curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" $PROD_URL
    ```

## Enabling dynamic developer deployments

In this section, you enable a unique URL for development branches in Git. Each
branch is represented by a URL that's identified by the branch name. Commits to
the branch trigger a deployment, and the updates are accessible at that same
URL.

1.  In Cloud Shell, set up the trigger:

    ```sh
    gcloud beta builds triggers create cloud-source-repositories \
      --trigger-config branch-trigger.json
    ```
2.  To review the trigger, go to the
    [Cloud Build Triggers page](https://console.cloud.google.com/cloud-build/triggers)
    in the Console.

    [Go to Triggers](https://console.cloud.google.com/cloud-build/triggers)

3.  In Cloud Shell, create a new branch:

    ```sh
    git checkout -b new-feature-1
    ```
4.  Open the sample application in the Cloud Shell:

    ```sh
    edit app.py
    ```
5.  In the sample application, modify the code to indicate v1.1 instead of v1.0:

    ```py
    @app.route('/')
    def hello_world():
        return 'Hello World v1.1'
    ```
6.  To return to your terminal, click **Open Terminal**.
7.  In Cloud Shell, commit the change and push to the remote
    repository:

    ```sh
    git add . && git commit -m "updated" && git push gcp new-feature-1
    ```
8.  To review the build in progress, go to the
    [Cloud Build Builds page](https://console.cloud.google.com/cloud-build/builds)
    in the Console.

    [Go to Builds](https://console.cloud.google.com/cloud-build/builds)

9.  After the build completes, to review the new revision, go to the
    [Cloud Run Revisions page](https://console.cloud.google.com/run/detail/us-central1/hello-cloudrun/revisions)
    in the Console.

    [Go to Revisions](https://console.cloud.google.com/run/detail/us-central1/hello-cloudrun/revisions)

10.  In Cloud Shell, get the unique URL for this branch:

    ```sh
    BRANCH_URL=$(gcloud run services describe hello-cloudrun  \
      --platform managed  \
      --region us-central1 \
      --format=json | jq \
      --raw-output ".status.traffic[] | select (.tag==\"new-feature-1\")|.url")
    echo $BRANCH_URL
    ```

11.  Access the authenticated URL:

    ```sh
    curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" $BRANCH_URL
    ```
    The updated response output looks like the following:

    ```none 
    Hello World v1.1
    ```

## Automating canary testing

When code is released to production, it's common to release code to a small
subset of live traffic before migrating all traffic to the new code base.

In this section, you implement a trigger that is activated when code is
committed to the main branch. The trigger deploys the code to a unique canary
URL and it routes 10% of all live traffic to the new revision.

1.  In Cloud Shell, set up the branch trigger:

    ```sh
    gcloud beta builds triggers create cloud-source-repositories \
      --trigger-config master-trigger.json
    ```
2.  To review the new trigger, go to the
    [Cloud Build Triggers page](https://console.cloud.google.com/cloud-build/triggers)
    in the Console.

    [Go to Triggers](https://console.cloud.google.com/cloud-build/triggers)

3.  In Cloud Shell, merge the branch to the main line and push to
    the remote repository:

    ```sh
    git checkout master
    git merge new-feature-1
    git push gcp master
    ```
4.  To review the build in progress, go to the
    [Cloud Build Builds page](https://console.cloud.google.com/cloud-build/builds)
    in the Console.

    [Go to Builds](https://console.cloud.google.com/cloud-build/builds)

5.  After the build is complete, to review the new revision, go to the
    [Cloud Run Revisions page](https://console.cloud.google.com/run/detail/us-central1/hello-cloudrun/revisions)
    in the Console.

    [Go to Revisions](https://console.cloud.google.com/run/detail/us-central1/hello-cloudrun/revisions)

    Now 90% of the traffic is routed to `prod`,
    10% to `canary`, and 0% to the branch revisions.


6.  Review the lines of `master-cloudbuild.yaml` that implement the logic for
    the canary deployment.

    The following lines deploy the new revision and use the `tag` flag to route
    traffic from the unique canary URL:

    ```sh 
    gcloud run deploy ${_SERVICE_NAME} \
      --platform managed \
      --region ${_REGION} \
      --image gcr.io/${PROJECT_ID}/${_SERVICE_NAME} \
      --tag=canary \
      --no-traffic
    ```
    The following line adds a static tag to the revision that notes the Git
    short SHA of the deployment:

    ```sh 
    gcloud beta run services update-traffic  ${_SERVICE_NAME} --update-tags=sha-$SHORT_SHA=$${CANARY}  --platform managed  --region ${_REGION}
    ```
    The following line updates the traffic to route 90% to production and 10% to
    canary:

    ```sh 
    gcloud run services update-traffic  ${_SERVICE_NAME} --to-revisions=$${PROD}=90,$${CANARY}=10  --platform managed  --region ${_REGION}
    ```
7.  In Cloud Shell, get the unique URL for the canary revision:

    ```sh
    CANARY_URL=$(gcloud run services describe hello-cloudrun \
      --platform managed \
      --region us-central1 \
      --format=json | jq \
      --raw-output ".status.traffic[] | select (.tag==\"canary\")|.url")
    echo $CANARY_URL
    ```
8.  Review the canary endpoint directly:

    ```sh
    curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" $CANARY_URL
    ```
9.  To see percentage-based responses, make a series of requests:

    ```sh
    LIVE_URL=$(gcloud run services describe hello-cloudrun \
      --platform managed \
      --region us-central1 \
      --format=json | jq \
      --raw-output ".status.url")

    for i in {0..20};do
        curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" $LIVE_URL; echo \n
    done
    ```

## Releasing to production

After the canary deployment is validated with a small subset of traffic, you
release the deployment to the remainder of the live traffic.

In this section, you set up a trigger that is activated when you create a tag
in the repository. The trigger migrates 100% of traffic to the already deployed
revision based on the commit SHA of the tag. Using the commit SHA ensures the
revision validated with canary traffic is the revision used for the remainder of
production traffic.

1.  In Cloud Shell, set up the tag trigger:

    ```sh
    gcloud beta builds triggers create cloud-source-repositories \
      --trigger-config tag-trigger.json
    ```
2.  To review the new trigger, go to the
    [Cloud Build Triggers page](https://console.cloud.google.com/cloud-build/triggers)
    in the Console.

    [Go to Triggers](https://console.cloud.google.com/cloud-build/triggers)

3.  In Cloud Shell, create a new tag and push to the remote repository:

    ```sh
    git tag 1.1
    git push gcp 1.1
    ```
4.  To review the build in progress, go to the
    [Cloud Build Builds page](https://console.cloud.google.com/cloud-build/builds)
    in the Console.

    [Go to Builds](https://console.cloud.google.com/cloud-build/builds)

5.  After the build is complete, to review the new revision, go to the
    [Cloud Run Revisions page](https://console.cloud.google.com/run/detail/us-central1/hello-cloudrun/revisions)
    in the Console.

    [Go to Revisions](https://console.cloud.google.com/run/detail/us-central1/hello-cloudrun/revisions)

    The revision is updated to indicate the
    `prod` tag and it is serving 100% of live traffic.

    
6.  In Cloud Shell, to see percentage-based responses, make a
    series of requests:

    ```sh
    LIVE_URL=$(gcloud run services describe hello-cloudrun \
      --platform managed \
      --region us-central1 \
      --format=json | jq \
      --raw-output ".status.url")

    for i in {0..20};do
        curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" $LIVE_URL; echo \n
    Done
    ```
7.  Review the lines of `tag-cloudbuild.yaml` that implement the production
    deployment logic.

    The following line updates the canary revision adding the `prod` tag. The
    deployed revision is now tagged for both `prod` and `canary`:

    ```sh 
    gcloud beta run services update-traffic  ${_SERVICE_NAME} --update-tags=prod=$${CANARY}  --platform managed  --region ${_REGION}
    ```
    The following line updates the traffic for the base service URL to route
    100% of traffic to the revision tagged as `prod`:

    ```sh 
    gcloud run services update-traffic  ${_SERVICE_NAME} --to-revisions=$${NEW_PROD}=100  --platform managed  --region ${_REGION}
    ```
