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

'use strict';

const config = require('../config');
const {PubSub} = require('@google-cloud/pubsub');

const GCLOUD_PROJECT = config.get('GCLOUD_PROJECT');

const pubsub = new PubSub({GCLOUD_PROJECT});
const topic = pubsub.topic('feedback');
const subscription = pubsub.subscription('worker-subscription');

function publishFeedback(feedback) {
  return topic.publish({
    data: feedback,
  });
}

function registerFeedbackNotification(cb) {
  subscription.on('message', cb);

  subscription.on('error', err => {
    console.error(err);
  });
}

function publishAnswer(answer) {
  return answersTopic.publish({
    data: answer
  });
}

// [START exports]
module.exports = {
  publishFeedback,
  publishAnswer,
  registerFeedbackNotification,
};
// [END exports]
