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

const {Datastore} = require('@google-cloud/datastore');
const config = require('./config');

// [START config]
const ds = new Datastore({
  projectId: config.get('GCLOUD_PROJECT')
});
const kind = 'Question';
// [END config]


// Lists all questions in a Quiz (defaults to 'gcp').
// Returns a promise
// [START list]
function list(quiz = 'gcp', redact = true) {
  const q = ds.createQuery([kind])
    .filter('quiz', '=', quiz);

  const p = ds.runQuery(q);

  return p.then(([results, { moreResults, endCursor }]) => {
    const questions = results.map(item => {
      item.id = item[Datastore.KEY].id;
      if (redact) {
        delete item.correctAnswer;
      }
      return item;
    });
    return {
      questions,
      nextPageToken: moreResults != 'NO_MORE_RESULTS' ? endCursor : false
    };
  });
}
// [END list]

// [START create]
function create({ quiz, author, title, answer1, answer2, answer3, answer4, correctAnswer, imageUrl }) {

  const key = ds.key(kind);

  const entity = {
    key,
    data: [
      { name: 'quiz', value: quiz },
      { name: 'author', value: author },
      { name: 'title', value: title },
      { name: 'answer1', value: answer1 },
      { name: 'answer2', value: answer2 },
      { name: 'answer3', value: answer3 },
      { name: 'answer4', value: answer4 },
      { name: 'correctAnswer', value: correctAnswer },
      { name: 'imageUrl', value: imageUrl },
    ]
  };
  return ds.save(entity);
}
// [END create]

// [START createMultiple]
async function createMultiple(...items) {

  const transaction = ds.transaction();

  transaction.run((err) => {
      for (let i = 0; i < items.length; i++) {
          let item = items[i];
          const key = ds.key([kind, item.id]);

          transaction.save({
              key: key,
              data: [
                  { name: 'quiz', value: item.quiz },
                  { name: 'author', value: item.author },
                  { name: 'title', value: item.title },
                  { name: 'answer1', value: item.answer1 },
                  { name: 'answer2', value: item.answer2 },
                  { name: 'answer3', value: item.answer3 },
                  { name: 'answer4', value: item.answer4 },
                  { name: 'correctAnswer', value: item.correctAnswer },
                  { name: 'imageUrl', value: item.imageUrl },
              ]
          });
      }

      transaction.commit((err) => {
          if (!err) {
              console.log("Entities created.")
          }
      });
  });
}
// [END createMultiple]

// [START exports]
module.exports = {
  create,
  createMultiple,
  list
};
// [END exports]
