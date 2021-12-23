(function () {

    var module = angular.module('qiqQuiz', ['ngRoute']);

    module.config(['$routeProvider', config]);


    function config($routeProvider) {
        $routeProvider.when('/quiz/:name', {
            controller: 'QuizController',
            controllerAs: 'qc',
            templateUrl: 'app/quizzes/quiz-template.html'
        });
    }


})();