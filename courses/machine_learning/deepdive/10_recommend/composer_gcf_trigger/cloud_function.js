'use strict';

const fetch = require('node-fetch');
const FormData = require('form-data');

/**
 * Triggered from a message on a Cloud Storage bucket.
 *
 * IAP authorization based on:
 * https://stackoverflow.com/questions/45787676/how-to-authenticate-google-cloud-functions-for-access-to-secure-app-engine-endpo
 * and
 * https://cloud.google.com/iap/docs/authentication-howto
 *
 * @param {!Object} event The Cloud Functions event.
 * @param {!Function} callback The callback function.
 */
exports.triggerDag = function triggerDag (event, callback) {
  // Fill in your Composer environment information here.

  // The project that holds your function
  const PROJECT_ID = ''; 
  // example: qwiklabs-gcp-97d55fb651b04b20

  // Navigate to your webserver's login page and get this from the URL
  const CLIENT_ID = '';
  // example: 954510698485-gde6id87qtdn9itl7809uj8s6a60n9gl

  // This should be part of your webserver's URL:
  // {tenant-project-id}.appspot.com
  const WEBSERVER_ID = '';
  // example: b93193d731fd74d3f-tp

  // The name of the DAG you wish to trigger
  const DAG_NAME = '';
  // example: GcsToBigQueryTriggered

  ///////////////////////
  // DO NOT EDIT BELOW //

  // Other constants
  const WEBSERVER_URL = `https://${WEBSERVER_ID}.appspot.com/api/experimental/dags/${DAG_NAME}/dag_runs`;
  const USER_AGENT = 'gcf-event-trigger';
  const BODY = {'conf': JSON.stringify(event.data)};

  // Make the request
  authorizeIap(CLIENT_ID, PROJECT_ID, USER_AGENT)
    .then(function iapAuthorizationCallback (iap) {
      makeIapPostRequest(WEBSERVER_URL, BODY, iap.idToken, USER_AGENT, iap.jwt);
    })
    .then(_ => callback(null))
    .catch(callback);
};

/**
   * @param {string} clientId The client id associated with the Composer webserver application.
   * @param {string} projectId The id for the project containing the Cloud Function.
   * @param {string} userAgent The user agent string which will be provided with the webserver request.
   */
function authorizeIap (clientId, projectId, userAgent) {
  const SERVICE_ACCOUNT = `${projectId}@appspot.gserviceaccount.com`;
  const JWT_HEADER = Buffer.from(JSON.stringify({alg: 'RS256', typ: 'JWT'}))
    .toString('base64');

  var jwt = '';
  var jwtClaimset = '';

  // Obtain an Oauth2 access token for the appspot service account
  return fetch(
    `http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/${SERVICE_ACCOUNT}/token`,
    {
      headers: {'User-Agent': userAgent, 'Metadata-Flavor': 'Google'}
    })
    .then(res => res.json())
    .then(function obtainAccessTokenCallback (tokenResponse) {
      if (tokenResponse.error) {
        return Promise.reject(tokenResponse.error);
      }
      var accessToken = tokenResponse.access_token;
      var iat = Math.floor(new Date().getTime() / 1000);
      var claims = {
        iss: SERVICE_ACCOUNT,
        aud: 'https://www.googleapis.com/oauth2/v4/token',
        iat: iat,
        exp: iat + 60,
        target_audience: clientId
      };
      jwtClaimset = Buffer.from(JSON.stringify(claims)).toString('base64');
      var toSign = [JWT_HEADER, jwtClaimset].join('.');

      return fetch(
        `https://iam.googleapis.com/v1/projects/${projectId}/serviceAccounts/${SERVICE_ACCOUNT}:signBlob`,
        {
          method: 'POST',
          body: JSON.stringify({'bytesToSign': Buffer.from(toSign).toString('base64')}),
          headers: {
            'User-Agent': userAgent,
            'Authorization': `Bearer ${accessToken}`
          }
        });
    })
    .then(res => res.json())
    .then(function signJsonClaimCallback (body) {
      if (body.error) {
        return Promise.reject(body.error);
      }
      // Request service account signature on header and claimset
      var jwtSignature = body.signature;
      jwt = [JWT_HEADER, jwtClaimset, jwtSignature].join('.');
      var form = new FormData();
      form.append('grant_type', 'urn:ietf:params:oauth:grant-type:jwt-bearer');
      form.append('assertion', jwt);
      return fetch(
        'https://www.googleapis.com/oauth2/v4/token', {
          method: 'POST',
          body: form
        });
    })
    .then(res => res.json())
    .then(function returnJwt (body) {
      if (body.error) {
        return Promise.reject(body.error);
      }
      return {
        jwt: jwt,
        idToken: body.id_token
      };
    });
}

/**
   * @param {string} url The url that the post request targets.
   * @param {string} body The body of the post request.
   * @param {string} idToken Bearer token used to authorize the iap request.
   * @param {string} userAgent The user agent to identify the requester.
   * @param {string} jwt A Json web token used to authenticate the request.
   */
function makeIapPostRequest (url, body, idToken, userAgent, jwt) {
  var form = new FormData();
  form.append('grant_type', 'urn:ietf:params:oauth:grant-type:jwt-bearer');
  form.append('assertion', jwt);

  return fetch(
    url, {
      method: 'POST',
      body: form
    })
    .then(function makeIapPostRequestCallback () {
      return fetch(url, {
        method: 'POST',
        headers: {
          'User-Agent': userAgent,
          'Authorization': `Bearer ${idToken}`
        },
        body: JSON.stringify(body)
      });
    });
}