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
(function () {

    var module = angular.module('qiqQuiz');

    module.factory('quizFactory', quizFactory);


    quizFactory.$inject = ['$http']

    function quizFactory($http) {
        var answers = [];

        return {
            getQuestions: getQuestions,
            sendAnswers: sendAnswers, 
            sendFeedback: sendFeedback, 
            addAnswer: addAnswer
        };

        function getQuestions(quizName) {
            return $http.get('/api/quizzes/' + quizName).then(function (response) {
                return response.data.questions;
            });
        }

        function addAnswer(email, questionId, selectedAnswer) {
            var answer = {
                email: email,
                id: questionId,
                answer: selectedAnswer,
                timestamp: Date.now()
            };
            answers.push(answer);
        }

        function sendAnswers(quizName) {
            return $http.post('/api/quizzes/' + quizName, answers).then(function (response) {
                return response.data;
            });
        }

        function sendFeedback(email, quiz, rating, feedback) {

        }
    }


})();