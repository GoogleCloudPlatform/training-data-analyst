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



// Lists all questions in a Quiz (defaults to 'gcp').
// Returns a promise
// [START list]
function list(quiz = 'gcp') {
  // Placeholder statement
  return Promise.resolve({
    questions: [{
      id: -1,
      title: 'Dummy question',
      answer1: 'Dummy answer1',
      answer2: 'Dummy answer2',
      answer3: 'Dummy answer3',
      answer4: 'Dummy answer4',
      correctAnswer: 2
    }],
    nextPageToken: 'NO_MORE_RESULTS'
  });
}
// [END list]

// [START create]
function create({ quiz, author, title, answer1, answer2, answer3, answer4, correctAnswer}) {
  // Placeholder statement
  return Promise.resolve({});
}
// [END create]

// [START exports]
module.exports = {
  create,
  list
};
// [END exports]
