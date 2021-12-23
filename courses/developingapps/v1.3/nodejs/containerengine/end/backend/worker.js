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
const subscriber = require('./gcp/pubsub');
const languageAPI = require('./gcp/languageapi');
const storage = require('./gcp/spanner');

console.log('Worker starting...');

function feedbackHandler(message) {
    console.log('Feedback received');
    try {
        var messageData = JSON.parse(message.toString());
        console.log(messageData);
        languageAPI.analyze(messageData.feedback)
        .then(score => {
            console.log(`Score: ${score}`);
            messageData.score = score;
            return messageData;
        })
        .then(storage.saveFeedback)
        .then(() => {
            console.log('Feedback saved');  
        }).catch(console.error);
    } catch { 
        console.log("Invalid feedback message- no JSON data:", message.toString()) 
    }

}
subscriber.registerFeedbackNotification(feedbackHandler);
console.log('Feedback registration complete...');
