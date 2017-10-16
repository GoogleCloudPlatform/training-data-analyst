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

// TODO: Load the ../config module



// END TODO

// TODO: Load the @google-cloud/datastore module



// END TODO

// TODO: Create a Datastore client object, ds
// The Datastore(...) factory function accepts an options // object which is used to specify which project's  
// Datastore should be used via the projectId property. 
// The projectId is retrieved from the config module. This // module retrieves the project ID from the GCLOUD_PROJECT // environment variable.




// END TODO

// TODO: Declare a constant named kind
//The Datastore key is the equivalent of a primary key in a // relational database.
// There are two main ways of writing a key:
// 1. Specify the kind, and let Datastore generate a unique //    numeric id
// 2. Specify the kind and a unique string id


// END TODO


// [START create]
function create({ quiz, author, title, answer1, answer2, answer3, answer4, correctAnswer }) {
  // TODO: Remove Placeholder statement

  return Promise.resolve({});

  // END TODO

  // TODO: Declare the entity key, 
  // with a Datastore generated id



  // END TODO

  // TODO: Declare the entity object, with the key and data


  // END TODO

  // TODO: Save the entity, return a promise
  // The ds.save(...) method returns a Promise to the  
  // caller, as it runs asynchronously.



  // END TODO

}
// [END create]


// Lists all questions in a Quiz (defaults to 'gcp').
// Returns a promise
// [START list]
function list(quiz = 'gcp') {
  // BONUS TODO: Remove Placeholder statement
  return Promise.resolve({
    questions: [{
      id: -1,
      title: 'Dummy question',
      answer1: 'Dummy answer1',
      answer2: 'Dummy answer2',
      answer3: 'Dummy answer3',
      answer4: 'Dummy answer4',
      correctAnswer: 2
    }],
    nextPageToken: 'NO_MORE_RESULTS'
  });
  // END TODO

  // BONUS TODO: Create the query
  // The Datastore client has a ds.createQuery() method that   
  // allows you to specify the kind(s) of entities to be 
  // retrieved.
  // The query can be customized to filter the Question 
  // entities for one quiz.




  // END TODO

  // BONUS TODO: Execute the query
  // The ds.runQuery() method returns a Promise as it runs 
  // asynchronously



  // END TODO

  // TODO: Return the transformed results
  // Cloud Datastore returns the query response as an array. 
  // The first element references the data, the second 
  // contains an object indicating if there are more results 
  // and provides a token to paginate through the results. 


  // TODO: For each question returned from Datastore


  // TODO: Add in an id property using the Entity id
  // The reason that we need to do this is that we want to 
  // know which question a student has answered (using the 
  // Entity's key gives a unique id) and to avoid giving the 
  // answer away in the JSON data.
  // Cloud Datastore references an entity's key using an 
  // ECMAScript symbol named Datastore.KEY. 
  // One way to reshape the data is to use the JavaScript
  // array map(...) method to apply the modification to each 
  // element in the array.



  // TODO: Remove the correctAnswer property


  // END TODO

  // TODO: return the transformed item


  // END TODO


  // Reshape the data


  // TODO: Return the questions

  // TODO: Return a property to allow the client
  // to request the next page of results

  // This will  pass the set of transformed entities back 
  // from the model to the client - in this case the Quiz 
  // application's API

}
// [END list]


// [START exports]
module.exports = {
  create,
  list
};
// [END exports]
