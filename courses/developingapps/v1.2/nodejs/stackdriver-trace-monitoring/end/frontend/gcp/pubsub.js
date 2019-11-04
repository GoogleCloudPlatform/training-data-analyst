// Copyright 2017, Google, Inc
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
const {PubSub} = require('@google-cloud/pubsub');

const pubsub = new PubSub({
  projectId: config.get('GCLOUD_PROJECT')
});

const feedbackTopic = pubsub.topic('feedback');
const answersTopic = pubsub.topic('answers');

function publishFeedback(feedback) {
  const dataBuffer=Buffer.from(JSON.stringify(feedback))
  return feedbackTopic.publish(dataBuffer);
}


function registerFeedbackNotification(cb) {

  feedbackTopic.createSubscription('feedback-subscription', { autoAck: true }, (err, feedbackSubscription) => {
    
    if (err && err.code == 6) {
      // subscription already exists
      console.log("Feedback subscription already exists");
      feedbackSubscription=feedbackTopic.subscription('feedback-subscription')
    }

    feedbackSubscription.get().then(results => {
        const subscription    = results[0];
        
        subscription.on('message', message => {
            cb(message.data);
        });

        subscription.on('error', err => {
            console.error(err);
        });
    }).catch(error => { console.log("Error getting feedback subscription", error)});

  });

}

function publishAnswer(answer) {
  const dataBuffer=Buffer.from(JSON.stringify(answer))
  return answersTopic.publish(dataBuffer);
}

function registerAnswerNotification(cb) {
    
  answersTopic.createSubscription('answer-subscription', { autoAck: true }, (err, answersSubscription) => {
    
    if (err && err.code == 6) {
        // subscription already exists
        console.log("Answer subscription already exists");
        answersSubscription = answersTopic.subscription('answer-subscription')
    }

  
    answersSubscription.get().then(results => {
        const subscription    = results[0];
        
        subscription.on('message', message => {
            cb(message.data);
        });

        subscription.on('error', err => {
            console.error(err);
        });
    }).catch(error => { console.log("Error getting answer subscription", error)});
    
  });
}
// [START exports]
module.exports = {
  publishAnswer,
  publishFeedback,
  registerFeedbackNotification,
  registerAnswerNotification
};
// [END exports]
