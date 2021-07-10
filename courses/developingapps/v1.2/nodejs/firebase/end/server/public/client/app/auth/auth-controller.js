(function () {

    var module = angular.module('qiqAuth');

    module.controller('AuthController', AuthController);

    AuthController.$inject = ['$location', 'authFactory']

    function AuthController($location, authFactory) {
        var ac = this;
        ac.register = register;
        init();

        function init() {
            
        }

        function register() {
            authFactory.register(ac.email, ac.password).then(function () {
                $location.path('/quiz/gcp');
            });
        }
    }
})();