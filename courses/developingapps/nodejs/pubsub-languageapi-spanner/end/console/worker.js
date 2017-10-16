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
const feedbackStorage = require('../server/gcp/spanner');

console.log('Worker starting...');

function handler(message) {
    console.log('Message received');
    console.log(message);

    languageAPI.analyze(message.data.feedback)
    .then(score => {
      console.log(`Score: ${score}`);
      message.data.score = score;
      return message.data;
    })
    .then(feedbackStorage.saveFeedback)
    .then(() => {
        console.log('Feedback saved');	
    });

}

subscriber.registerFeedbackNotification(handler);
