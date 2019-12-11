// Copyright 2017, Google, Inc.
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//    http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// Import the config module
const config = require('../config');

// TODO: Load the Natural Language ML API module
const Language = require('@google-cloud/language');

// END TODO

// TODO: Create a client object against the Language API
// using the Language.LanguageServiceClient function
// The LanguageServiceClient function accepts an options 
// object which is used to specify which project should be 
// billed for use of the API via the projectId property. 
// The projectId is retrieved from the config module. 
// This module retrieves the project ID from the 
// GCLOUD_PROJECT environment variable.

const language = new Language.LanguageServiceClient({
    projectId: config.get('GCLOUD_PROJECT')
});

// END TODO

function analyze(text) {
    // TODO: Create an object named document with the 
    // correct structure for the Natural Language ML API
    // TODO: Initialize object content & type properties
    // TODO: Set content from text arg
    // TODO: Set type to PLAIN_TEXT
    const document = {
        content: text,
        type: 'PLAIN_TEXT'
    };

    // END TODO

    // TODO: Perform sentiment detection
    return language.analyzeSentiment({ document })
    // TODO: Chain then
    // When the results come back
    // The sentiment data is the first element
       .then(results => {
          const sentiment = results[0];
          // TODO: Get the sentiment score (-1 to +1)
          return sentiment.documentSentiment.score;
       });
    // END TODO
}


module.exports = {
    analyze
};