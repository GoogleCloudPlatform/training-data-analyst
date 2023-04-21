// Copyright 2023 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

const express = require('express');

const app = express();
app.use(express.json());

// When used as a destination for Eventarc running in Cloud Run,
// the sent event HTTP request will be logged.
app.post('/', async (req, res) => {
  // safely retrieve event type
  var eventType = "ce-type header not found"
  try { eventType = req.headers["ce-type"]; } catch(e) {}

  console.log("EVENT RECEIVED (%s)", eventType);
  console.log("HEADERS (EXCEPT AUTH):");
  delete req.headers.authorization; // do not log auth header
  console.log(JSON.stringify(req.headers));
  console.log("BODY:");
  console.log(JSON.stringify(req.body));
  res.status(200).send({
    headers: req.headers,
    body: req.body
  });
});

const port = parseInt(process.env.PORT) || 8080;
app.listen(port, () => {
  console.log("eventarc-event-logger: listening on port", port);
});
