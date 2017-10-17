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

const config = require('../config');

// TODO: Load the module for Cloud Storage



// END TODO

// TODO: Create the storage client
// The Storage(...) factory function accepts an options 
// object which is used to specify which project's Cloud 
// Storage buckets should be used via the projectId
// property. 
// The projectId is retrieved from the config module. 
// This module retrieves the project ID from the 
// GCLOUD_PROJECT environment variable.




// END TODO

// TODO: Get the GCLOUD_BUCKET environment variable
// Recall that earlier you exported the bucket name into an 
// environment variable.
// The config module provides access to this environment 
// variable so you can use it in code



// END TODO

// TODO: Get a reference to the Cloud Storage bucket



// END TODO


// Express middleware that will automatically pass uploads to Cloud Storage.
// req.file is processed and will have a new property:
// * ``cloudStoragePublicUrl`` the public url to the object.
// [START sendUploadToGCS]
function sendUploadToGCS(req, res, next) {
  // The existing code in the handler checks to see if there 
  // is a file property on the HTTP request - if a file has 
  // been uploaded, then Multer will have created this 
  // property in the preceding middleware call.
  if (!req.file) {
    return next();
  }
  // In addition, a unique object name, oname,  has been 
  // created based on the file's original name. It has a 
  // prefix generated using the current date and time.
  // This should ensure that a new file upload won't 
  // overwrite an existing object in the bucket
  const oname = Date.now() + req.file.originalname;

  // TODO: Get a reference to the new object



  // END TODO

  // TODO: Create a stream to write the file into 
  // Cloud Storage
  // The uploaded file's MIME type can be retrieved using 
  // req.file.mimetype.
  // Cloud Storage metadata can be used for many purposes, 
  // including establishing the type of an object.






  // END TODO


  // TODO: Attach two event handlers (1) error
  // Event handler if there's an error when uploading

  // TODO: If there's an error move to the next handler



  // END TODO


  // END TODO


  // TODO: Attach two event handlers (2) finish
  // The upload completed successfully


  // TODO: Make the object publicly accessible


  // TODO: Set a new property on the file for the
  // public URL for the object
  // Cloud Storage public URLs are in the form:
  // https://storage.googleapis.com/[BUCKET]/[OBJECT]
  // Use an ECMAScript template literal (`https://...`)to 
  // populate the URL with appropriate values for the bucket 
  // ${GCLOUD_BUCKET} and object name ${oname}



  // END TODO

  // TODO: Invoke the next middleware handler



  // END TODO


  // END TODO


  // TODO: Upload the file's data into Cloud Storage




  // END TODO


}
// [END sendUploadToGCS]

// Multer handles parsing multipart/form-data requests.
// This instance is configured to store images in memory.
// This makes it straightforward to upload to Cloud Storage.
// [START multer]
const Multer = require('multer');
const multer = Multer({
  storage: Multer.MemoryStorage,
  limits: {
    fileSize: 40 * 1024 * 1024 // no larger than 40mb
  }
});
// [END multer]

module.exports = {
  sendUploadToGCS,
  multer
};
