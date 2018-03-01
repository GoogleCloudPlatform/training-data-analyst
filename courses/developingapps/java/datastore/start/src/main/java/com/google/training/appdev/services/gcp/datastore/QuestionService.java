/*
 * Copyright 2018 Google Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.google.training.appdev.services.gcp.datastore;

// TODO: Import the com.google.cloud.datastore.* package



// END TODO

import com.google.training.appdev.services.gcp.domain.Question;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

import org.springframework.stereotype.Service;

@Service
public class QuestionService {

// TODO: Create a Datastore client object, datastore
// The DatastoreOptions class has a getDefaultInstance()
// static method.
// Use the getService() method of the DatastoreOptions
// object to get the Datastore client


// END TODO

// TODO: Declare a static final String named kind
//The Datastore key is the equivalent of a primary key in a // relational database.
// There are two main ways of writing a key:
// 1. Specify the kind, and let Datastore generate a unique //    numeric id
// 2. Specify the kind and a unique string id



// END TODO

// TODO: Create a KeyFactory for Question entities


// END TODO

// The createQuestion(Question question) method 
// is passed a Question object using data from the form
// Extract the form data and add it to Datastore

// TODO: Modify return type to Key

    public String createQuestion(Question question) {

// END TODO

// TODO: Declare the entity key, 
// with a Datastore allocated id


// END TODO
 
// TODO: Declare the entity object, with the key and data
// The entity's members are set using the Entity.Builder. 
// This has a set method for property names and values
// Values are retrieved from the Domain object






// END TODO

// TODO: Save the entity

// END TODO

// TODO: Return the key

        return "Replace this string with the key";

// END TODO
    }

    public List<Question> getAllQuestions(String quiz){

// TODO: Remove this code

        List<Question> questions = new ArrayList<>();
        Question dummy = new Question.Builder()
                .withQuiz("gcp")
                .withAuthor("Dummy Author")
                .withTitle("Dummy Title")
                .withAnswerOne("Dummy Answer One")
                .withAnswerTwo("Dummy Answer Two")
                .withAnswerThree("Dummy Answer Three")
                .withAnswerFour("Dummy Answer Four")
                .withCorrectAnswer(1)
                .withId(-1)
                .build();
        questions.add(dummy);

        return questions;

// END TODO

 // TODO: Create the query
 // The Query class has a static newEntityQueryBuilder() 
 // method that allows you to specify the kind(s) of 
 // entities to be retrieved.
 // The query can be customized to filter the Question 
 // entities for one quiz.


 // END TODO

 // TODO: Execute the query
 // The datastore.run(query) method returns an iterator
 // for entities


 // END TODO

 // TODO: Return the transformed results
 // Use the buildQuestions(entities) method to convert
 // from Datastore entities to domain objects



 // END TODO

    }


/* TODO: Uncomment this block

    private List<Question> buildQuestions(Iterator<Entity> entities){
        List<Question> questions = new ArrayList<>();
        entities.forEachRemaining(entity-> questions.add(entityToQuestion(entity)));
        return questions;
    }

    private Question entityToQuestion(Entity entity){
        return new Question.Builder()
                .withQuiz(entity.getString(Question.QUIZ))
                .withAuthor(entity.getString(Question.AUTHOR))
                .withTitle(entity.getString(Question.TITLE))
                .withAnswerOne(entity.getString(Question.ANSWER_ONE))
                .withAnswerTwo(entity.getString(Question.ANSWER_TWO))
                .withAnswerThree(entity.getString(Question.ANSWER_THREE))
                .withAnswerFour(entity.getString(Question.ANSWER_FOUR))
                .withCorrectAnswer(entity.getLong(Question.CORRECT_ANSWER))
                .withId(entity.getKey().getId())
                .build();
    }

*/
}
