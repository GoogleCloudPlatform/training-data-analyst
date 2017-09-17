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
// TODO: Add the following statement to import and start
// Stackdriver debug-agent
// The start(...) method takes an 'options' object that you 
// can use to configure the Stackdriver Debugger agent.
// You will need to pass through an object with an 
// allowExpressions Boolean property set to true.




// END TODO
// TODO: Load the error-reporting module




// END TODO



const path = require('path');
const express = require('express');
const config = require('./config');

const app = express();

// TODO: Create the errorReporting client object




// END TODO


// Static files
app.use(express.static('public/'));

app.disable('etag');
app.set('views', path.join(__dirname, 'web-app/views'));
app.set('view engine', 'pug');
app.set('trust proxy', true);
app.set('json spaces', 2);

// Questions
app.use('/questions', require('./web-app/questions'));

// Quizzes API
app.use('/api/quizzes', require('./api'));

// Display the home page
app.get('/', (req, res) => {
  res.render('home.pug');
});

// TODO: Use Stackdriver Error Reporting 
// middleware for Express




// END TODO


// Basic 404 handler
app.use((req, res) => {
  res.status(404).send('Not Found');
});

// Basic error handler
app.use((err, req, res, next) => {
  /* jshint unused:false */
  console.error(err);
  // If our routes specified a specific response, then send that. Otherwise,
  // send a generic message so as not to leak anything.
  res.status(500).send(err.response || 'Something broke!');
});

if (module === require.main) {
  // Start the server
  const server = app.listen(config.get('PORT'), () => {
    const port = server.address().port;
    console.log(`App listening on port ${port}`);
  });
}

module.exports = app;
