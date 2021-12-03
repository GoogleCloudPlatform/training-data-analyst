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

            });
        }
    }
})();