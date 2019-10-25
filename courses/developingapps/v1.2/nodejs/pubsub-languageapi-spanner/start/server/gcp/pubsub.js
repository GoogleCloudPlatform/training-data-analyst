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
const config = require('../config');

// TODO: Load the Cloud Pub/Sub module



// END TODO

// TODO: Create a client object against Cloud Pub/Sub
// The Pubsub(...) factory function accepts an options 
// object which is used to specify which project's Cloud 
// Pub/Sub topics should be used via the projectId 
// property. 
// The projectId is retrieved from the config module. 
// This module retrieves the project ID from the 
// GCLOUD_PROJECT environment variable.




// END TODO

// TODO: Get a reference to the feedback topic
// This code assumes that the topic is already present in 
// the project. 
// If it isn't then you would need to handle that case by 
// using the pubsub object's createTopic(...) method



// END TODO


function publishFeedback(feedback) {
  // TODO: Publish a message to the feedback topic
  // This runs asynchronously so you need to return the 
  // Promise that results from executing topic.publish(...)
  // The feedback object must be converted to a buffer
  // In addition, it's a good idea to use a consistent 
  // property for the message body. This lab will use the 
  // name dataBuffer for the message data





  // END TODO

}

// The worker application will pass a callback to this 
// method as the cb argument so it is notified when 
// feedback is received
function registerFeedbackNotification(cb) {
  // TODO: Create a subscription called worker-subscription
  // TODO: Have it auto-acknowledge messages and trap errors
  // TODO: err.code == 6 means subscription already exists


  // TODO: Create a subscription object for worker-subscription 
  // Then use the get() method to call the API request to 
  // return a promise


  // END TODO

  // The results argument in the promise is an array - the 
  // first element in this array is the subscription object.

  // TODO: Declare a subscription constant



  // END TODO

  // TODO: Register an event handler for message events
  // TODO: Use an arrow function to handle the event


  // TODO: When a message arrives, invoke a callback




  // END TODO


  // TODO: Register an event handler for error event
  // TODO: Print the error to the console


  // END TODO

  // Add a final catch to the promise chain to handle errors


  // END TODO

}

// [START exports]
module.exports = {
  publishFeedback,
  registerFeedbackNotification
};
// [END exports]
