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

// Automatically parse request body as form data
router.use(bodyParser.urlencoded({ extended: false }));

// Set Content-Type for all responses for these routes
router.use((req, res, next) => {
  res.set('Content-Type', 'text/html');
  next();
});

/**
 * GET /questions
 *
 * Display a page of questions (up to ten at a time).
 */
router.get('/', (req, res, next) => {
  model.list(10, req.query.pageToken)
    .then(([results, { moreResults, endCursor }]) => {
      console.log([results, { moreResults, endCursor }]);
      res.render('questions/list.pug', {
        questions: results,
        nextPageToken: moreResults ? endCursor : false
      });
    }, err => { next(err) });
});

/**
 * GET /questions/add
 *
 * Display a form for creating a question.
 */
// [START add_get]
router.get('/add', (req, res) => {
  res.render('questions/add.pug', {
    question: {},
    categories: ['gcp', 'people', 'places'],
    action: 'Add'
  });
});
// [END add_get]

/**
 * POST /questions/add
 *
 * Create a question.
 */
// This handler receives data submitted by authors creating new questions
// The form post data has been extracted from the HTTP Request body using the Express body parser and assigned to a const identifier called data
// The handler delegates to a model object's create() method which receives the form post data
// The handler also redirects back to the home page after a question has been added
// [START add_post]
router.post('/add',
  (req, res, next) => {
    let data = req.body;

    // Save the data to the database.
    model.create(data)
      .then(entity => { res.redirect('/') })
      .catch(err => {
        next(err);
        return;
      });
  });
// [END add_post]



/**
 * GET /questions/:id
 *
 * Display a question.
 */
router.get('/:question', (req, res, next) => {
  model.read(req.params.question, (err, entity) => {
    if (err) {
      next(err);
      return;
    }
    res.render('questions/view.pug', {
      question: entity
    });
  });
});

/**
 * Errors on "/questions/*" routes.
 */
router.use((err, req, res, next) => {
  // Format error and forward to generic error handler for logging and
  // responding to the request
  err.response = err.message;
  next(err);
});

module.exports = router;
