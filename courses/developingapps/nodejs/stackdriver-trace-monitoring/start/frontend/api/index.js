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

const express = require('express');
const bodyParser = require('body-parser');

const model = require('../gcp/datastore');
const publisher = require('../gcp/pubsub');

const router = express.Router();

// Automatically parse request body as JSON
router.use(bodyParser.json());

/**
 * GET /api/quizzes/:quiz
 *
 * Retrieve all the questions in the quiz.
 */
router.get('/:quiz', (req, res, next) => {

  model.list(req.params.quiz)
    .then(data => {
      res.status(200).json(data);
    }, err => { next(err) });
});


/**
 * POST /api/quizzes/:quiz
 *
 * Submit the quiz answers, return a score.
 */
router.post('/:quiz', (req, res, next) => {
  const answers = req.body; // in the form [{id, answer}]
  console.log(answers);
  model.list(req.params.quiz, false)
    .then(response => {
      const { questions } = response;

      const answersWithCorrect = answers.map(({ id, email, quiz, answer, timestamp }) => {
        const theQuestion = questions.find(q => q.id == id);
        return { id, email, quiz: theQuestion.quiz, answer, correct: theQuestion.correctAnswer, timestamp };
      });

      // Executes a set of promises in sequence
      const sequence = funcs =>
        funcs.reduce((promise, func) =>
          promise.then(result => func().then(Array.prototype.concat.bind(result))), Promise.resolve([]));


      const parallel = funcs => Promise.all(funcs.map(func => func()));

      // TODO: Sends the answers to Pub/Sub in parallel 
      // Sends the answers to Pub/Sub in sequence
      // Change sequence to parallel in the next statement

      sequence(answersWithCorrect.map(answer => () => publisher.publishAnswer(answer))).then(() => {
        // Waits until all the Pub/Sub messages have been acknowledged before returning to the client
        const score = answersWithCorrect.filter(a => a.answer == a.correct).length;
        res.status(200).json({ correct: score, total: questions.length });
      });

      // END TODO

    }, err => { next(err) });
});

/**
 * POST /api/quizzes/feedback/:quiz
 *
 * Submit the quiz feedback, get a response
 */
router.post('/feedback/:quiz', (req, res, next) => {
  const feedback = req.body; // in the form [{id, answer}]
  console.log(feedback);
  publisher.publishFeedback(feedback).then(() => {
    res.json('Feedback received');
  }).catch(err => {
    next(err);
  });

});


/**
 * Errors on "/api/questions/*" routes.
 */
router.use((err, req, res, next) => {
  // Format error and forward to generic error handler for logging and
  // responding to the request
  err.response = {
    message: err.message,
    internalCode: err.code
  };
  next(err);
});

module.exports = router;
