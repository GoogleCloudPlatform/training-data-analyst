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

// TODO: Load the ./languageapi module

const languageAPI = require('./languageapi');

// END TODO

// TODO: Load the ./spanner module

const feedbackStorage = require('./spanner');

// END TODO


exports.subscribe = function subscribe(event) {
  // The Cloud Pub/Sub Message object.
  const pubsubMessage = event.data;

  // TODO: Decode the Cloud Pub/Sub message
  // extracting the feedbackObject data
  // The message received from Pub/Sub is base64 encoded, and 
  // the data submitted by students is in a data property

  let feedbackObject = JSON.parse(Buffer.from(
        pubsubMessage.data, 'base64').toString());

return languageAPI.analyze(feedbackObject.feedback)
    .then(
      score => {
        // TODO: Log the sentiment score
  	   
        console.log(`Score: ${score}`);

        // END TODO

        // TODO: Add new score property to feedbackObject

  	   feedbackObject.score = score;

        // END TODO

        // TODO: Pass feedback object to the next handler

  	   return feedbackObject;

        // END TODO
      }) // TODO: insert record
    .then(feedbackStorage.saveFeedback) 
    .then(() => {
       // TODO: Log and return success

 	  console.log('feedback saved...');
	  return 'success';  
  
       // END TODO
	
    }).catch(console.error); // TODO: Log error

};


