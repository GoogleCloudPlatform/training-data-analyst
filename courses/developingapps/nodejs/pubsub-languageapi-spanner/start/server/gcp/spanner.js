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
const config = require('../config');

// TODO: Import the @google-cloud/spanner module



// END TODO

// TODO: Create a client object to access Cloud Spanner
// The Spanner(...) factory function accepts an options 
// object which is used to select which project's Cloud 
// Spanner database instance(s) should be used via the 
// projectId property. 
// The projectId is retrieved from the config module. 
// This module retrieves the project ID from the 
// GCLOUD_PROJECT environment variable.





// END TODO

// TODO: Get a reference to the Cloud Spanner instance



// END TODO

// TODO: Get a reference to the Cloud Spanner database



// END TODO

// TODO: Get a reference to the Cloud Spanner table




// END TODO



function saveFeedback({ email, quiz, timestamp, rating, feedback, score }) {
    // TODO: Declare rev_email constant
    // TODO: Produce a 'reversed' email address
    // eg app.dev.student@example.org -> org_example_student_dev_app



    // END TODO

    // TODO: Create record object to be inserted into Spanner





    // END TODO

    // TODO: Insert the record into the table




    // END TODO



}

module.exports = {
    saveFeedback
};