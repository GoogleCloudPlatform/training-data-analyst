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
      const {questions} = response;
      const score = questions.map(q => {
        return answers.filter(a => a.id == q.id && q.correctAnswer == a.answer).length // 0 if incorrect, 1 if correct
      }).filter(item => item === 1).length; // number of correct answers

      res.status(200).json({correct:score, total: questions.length});
    }, err => { next(err) });
});

/**
 * POST /api/quizzes/feedback/:quiz
 *
 * Submit the quiz answers, return a score.
 */
router.post('/feedback/:quiz', (req, res, next) => {
  const feedback = req.body; // in the form [{id, answer}]
  console.log(feedback);

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
