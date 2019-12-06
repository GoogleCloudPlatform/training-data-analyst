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
            // return $http.post('/api/quizzes/sendFeedback', {
            //     email: email,
            //     quiz: quiz,
            //     rating: rating,
            //     feedback: feedback
            // }).then(function (response) {
            //     return response.data; 
            // });
        }
    }


})();