(function () {

    var module = angular.module('qiqAuth', ['ngRoute', 'firebase']);

    module.config(['$routeProvider', config]);


    function config($routeProvider) {
        $routeProvider.when('/register', {
            controller: 'AuthController',
            controllerAs: 'ac',
            templateUrl: 'app/auth/auth-register-template.html'
        });
    }


})();