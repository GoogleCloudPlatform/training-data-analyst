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
package com.google.training.appdev.services.gcp.domain;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonRootName;
import org.springframework.web.multipart.MultipartFile;

@JsonRootName(value = "questions")
public class Question {
    private String quiz;
    private String author;
    private String title;
    private String answerOne;
    private String answerTwo;
    private String answerThree;
    private String answerFour;
    private long correctAnswer;
    private String imageUrl="";
    private MultipartFile image;
    private long id;

    public static final String QUIZ = "quiz";
    public static final String AUTHOR = "author";
    public static final String TITLE = "title";
    public static final String ANSWER_ONE = "answerOne";
    public static final String ANSWER_TWO = "answerTwo";
    public static final String ANSWER_THREE = "answerThree";
    public static final String ANSWER_FOUR = "answerFour";
    public static final String IMAGE_URL = "imageUrl";
    public static final String CORRECT_ANSWER = "correctAnswer";


    private Question(Builder builder){
        this.quiz = builder.quiz;
        this.author = builder.author;
        this.title = builder.title;
        this.answerOne = builder.answerOne;
        this.answerTwo = builder.answerTwo;
        this.answerThree = builder.answerThree;
        this.answerFour = builder.answerFour;
        this.correctAnswer = builder.correctAnswer;
        this.imageUrl = builder.imageUrl;
        this.id = builder.id;
    }

    public static class Builder {
        private String quiz;
        private String author;
        private String title;
        private String answerOne;
        private String answerTwo;
        private String answerThree;
        private String answerFour;
        private long correctAnswer;
        private String imageUrl;
        private long id;

        public Builder withQuiz(String quiz){
            this.quiz = quiz;
            return this;
        }

        public Builder withAuthor(String author){
            this.author = author;
            return this;
        }

        public Builder withTitle(String title){
            this.title = title;
            return this;
        }

        public Builder withAnswerOne(String answerOne){
            this.answerOne = answerOne;
            return this;
        }

        public Builder withAnswerTwo(String answerTwo){
            this.answerTwo = answerTwo;
            return this;
        }

        public Builder withAnswerThree(String answerThree){
            this.answerThree = answerThree;
            return this;
        }

        public Builder withAnswerFour(String answerFour){
            this.answerFour = answerFour;
            return this;
        }

        public Builder withCorrectAnswer(long correctAnswer){
            this.correctAnswer = correctAnswer;
            return this;
        }

        public Builder withImageUrl(String imageUrl){
            this.imageUrl = imageUrl;
            return this;
        }

        public Builder withId(long id){
            this.id = id;
            return this;
        }

        public Question build(){
            return new Question(this);
        }
    }

    public Question(){

    }



    public long getId() {
        return id;
    }

    public void setId(long id) {
        this.id = id;
    }

    public String getQuiz() {
        return quiz;
    }

    public void setQuiz(String quiz) {
        this.quiz = quiz;
    }

    public String getAuthor() {
        return author;
    }

    public void setAuthor(String author) {
        this.author = author;
    }

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    @JsonProperty("answer1")
    public String getAnswerOne() {
        return answerOne;
    }

    public void setAnswerOne(String answerOne) {
        this.answerOne = answerOne;
    }

    @JsonProperty("answer2")
    public String getAnswerTwo() {
        return answerTwo;
    }

    public void setAnswerTwo(String answerTwo) {
        this.answerTwo = answerTwo;
    }

    @JsonProperty("answer3")
    public String getAnswerThree() {
        return answerThree;
    }

    public void setAnswerThree(String answerThree) {
        this.answerThree = answerThree;
    }

    public String getAnswerFour() {
        return answerFour;
    }

    @JsonProperty("answer4")
    public void setAnswerFour(String answerFour) {
        this.answerFour = answerFour;
    }

    public long getCorrectAnswer() {
        return correctAnswer;
    }

    public void setCorrectAnswer(long correctAnswer) {
        this.correctAnswer = correctAnswer;
    }

    public String getImageUrl() {
        return imageUrl;
    }

    public void setImageUrl(String imageUrl) {
        this.imageUrl = imageUrl;
    }

    public MultipartFile getImage() {
        return image;
    }

    public void setImage(MultipartFile image) {
        this.image = image;
    }

    @Override
    public String toString() {
        return "Question{" +
                "quiz='" + quiz + '\'' +
                ", author='" + author + '\'' +
                ", title='" + title + '\'' +
                ", answerOne='" + answerOne + '\'' +
                ", answerTwo='" + answerTwo + '\'' +
                ", answerThree='" + answerThree + '\'' +
                ", answerFour='" + answerFour + '\'' +
                ", correctAnswer=" + correctAnswer +
                ", imageUrl='" + imageUrl + '\'' +
                ", id=" + id +
                '}';
    }
}
