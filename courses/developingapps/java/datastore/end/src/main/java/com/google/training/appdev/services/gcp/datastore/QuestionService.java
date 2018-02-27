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

import com.google.cloud.datastore.*;
import com.google.training.appdev.services.gcp.domain.Question;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

import org.springframework.stereotype.Service;

@Service
public class QuestionService {


    private Datastore datastore = DatastoreOptions.getDefaultInstance().getService();
    private static final String ENTITY_KIND = "Question";
    private final KeyFactory keyFactory = datastore.newKeyFactory().setKind(ENTITY_KIND);

    public Key createQuestion(Question question){
        Key key = datastore.allocateId(keyFactory.newKey());
        Entity questionEntity = Entity.newBuilder(key)
                .set(Question.QUIZ, question.getQuiz())
                .set(Question.AUTHOR, question.getAuthor())
                .set(Question.TITLE, question.getTitle())
                .set(Question.ANSWER_ONE,question.getAnswerOne())
                .set(Question.ANSWER_TWO, question.getAnswerTwo())
                .set(Question.ANSWER_THREE,question.getAnswerThree())
                .set(Question.ANSWER_FOUR, question.getAnswerFour())
                .set(Question.CORRECT_ANSWER, question.getCorrectAnswer())
                .build();
        datastore.put(questionEntity);
        return key;
    }

    public List<Question> getAllQuestions(String quiz){

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

        return null;

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
