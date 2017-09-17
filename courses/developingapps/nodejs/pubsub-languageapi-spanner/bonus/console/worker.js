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
const subscriber = require('../server/gcp/pubsub');
const languageAPI = require('../server/gcp/languageapi');
const storage = require('../server/gcp/spanner');

console.log('Worker starting...');

function feedbackHandler(message) {
    console.log('Feedback received');
    console.log(message);

    languageAPI.analyze(message.data.feedback)
    .then(score => {
      console.log(`Score: ${score}`);
      message.data.score = score;
      return message.data;
    })
    .then(storage.saveFeedback)
    .then(() => {
        console.log('Feedback saved');	
    });

}


function answerHandler(message) {
    console.log('Answer received');
    console.log(message);

    storage.saveAnswer(message.data)
    .then(() => {
        console.log('Answer saved');	
    });

}
subscriber.registerFeedbackNotification(feedbackHandler);
console.log('Feedback registration complete...');
subscriber.registerAnswerNotification(answerHandler);
console.log('Answer registration complete...');