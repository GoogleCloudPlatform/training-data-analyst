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
const storage = require('./gcp/spanner');

console.log('Answer worker starting...');

function handler(message) {
    console.log('Message received');
    console.log(message.data);

    storage.saveAnswer(message.data)
    .then(() => {
        console.log('Answer saved');	
    }).catch(console.error);

}

subscriber.registerAnswerNotification(handler);
