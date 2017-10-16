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

const ds_client = require('../server/gcp/datastore');

const questions = [
    {
        quiz: 'gcp',
        author: 'Nigel',
        title: 'Which company runs GCP?',
        answer1: 'Amazon',
        answer2: 'Google',
        answer3: 'IBM',
        answer4: 'Microsoft',
        correctAnswer: 2,
        imageUrl: ''
    },
    {
        quiz: 'gcp',
        author: 'Nigel',
        title: 'Which GCP product is NoSQL?',
        answer1: 'Compute Engine',
        answer2: 'Datastore',
        answer3: 'Spanner',
        answer4: 'BigQuery',
        correctAnswer: 2,
        imageUrl: ''
    },
    {
        quiz: 'gcp',
        author: 'Nigel',
        title: 'Which GCP product is an Object Store?',
        answer1: 'Cloud Storage',
        answer2: 'Datastore',
        answer3: 'Big Table',
        answer4: 'All of the above',
        correctAnswer: 1,
        imageUrl: ''
    },
    {
        quiz: 'places',
        author: 'Nigel',
        title: 'What is the capital of France?',
        answer1: 'Berlin',
        answer2: 'London',
        answer3: 'Paris',
        answer4: 'Stockholm',
        correctAnswer: 3,
        imageUrl: ''
    },
];

questions.forEach(item => {
    ds_client.create(item);
});