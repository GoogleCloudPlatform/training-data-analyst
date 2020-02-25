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

    module.controller('QuizController', QuizController);

    QuizController.$inject = ['$routeParams', 'quizFactory', 'authFactory'];

    function QuizController($routeParams, quizFactory, authFactory) {
        var qc = this;
        var currentQuestionIndex = 0;

        qc.quizName = $routeParams.name || 'gcp';
        qc.user = authFactory.user;
        qc.selectAnswer = selectAnswer;
        qc.sendFeedback = sendFeedback;
        qc.questions = null;
        qc.gameOver = false;
        qc.feedbackSent = false;
        qc.rating = -1;

        init();

        function init() {
            quizFactory.getQuestions(qc.quizName).then(function (data) {
                qc.questions = data;
                qc.question = qc.questions[currentQuestionIndex];
            });
        }

        function selectAnswer() {
            quizFactory.addAnswer(qc.user.email, qc.question.id, qc.selectedAnswer);
            qc.selectedAnswer = -1;
            currentQuestionIndex++;
            if (currentQuestionIndex == qc.questions.length) {
                quizFactory.sendAnswers(qc.quizName).then(function (data) {
                    qc.correct = data.correct;
                    qc.total = data.total;
                    qc.gameOver = true;
                });
            } else {
                qc.question = qc.questions[currentQuestionIndex];
            }
        }

        function sendFeedback() {
            console.log({email:qc.user.email, quizName:qc.quizName, rating:qc.rating, feedback:qc.feedback});
            quizFactory.sendFeedback(qc.user.email, qc.quizName, qc.rating, qc.feedback).then(function (data) {
                qc.feedbackSent = true;
            });
        }
    }
})();