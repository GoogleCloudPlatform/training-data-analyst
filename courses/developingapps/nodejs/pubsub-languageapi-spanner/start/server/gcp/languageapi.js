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

// TODO: Load the Natural Language ML API module




// END TODO

// TODO: Create a client object against the Language API
// The Language(...) factory function accepts an options 
// object which is used to specify which project should be 
// billed for use of the API via the projectId property. 
// The projectId is retrieved from the config module. 
// This module retrieves the project ID from the 
// GCLOUD_PROJECT environment variable.





// END TODO


function analyze(text) {
    // TODO: Create an object named document with the 
    // correct structure for the Natural Language ML API


    // TODO: Initialize object content and type props
    // TODO: Set content from text arg
    // TODO: Set type to PLAIN_TEXT


    // END TODO

    // TODO: Perform sentiment detection

    // TODO: Chain then
    // When the results come back
    // The sentiment data is the first element


    // TODO: Get the sentiment score (-1 to +1)



    // END TODO

}

module.exports = {
    analyze
};