const config = require('../server/config');
const iamPolicies = require('../iam.json');
const fs = require('fs');

const GCLOUD_PROJECT = config.get('GCLOUD_PROJECT');
const serviceAccountEmail = `serviceAccount:quiz-account@${GCLOUD_PROJECT}.iam.gserviceaccount.com`;

iamPolicies.bindings.push({
    members: [
        serviceAccountEmail
    ],
    role: 'roles/owner'
});

const newPolicies = JSON.stringify(iamPolicies)

fs.writeFileSync('./iam_modified.json', newPolicies);