(function () {

    var module = angular.module('qiqAuth');

    module.component('qiqLogin', {
        controller: LoginComponentController,
        templateUrl: 'app/auth/qiq-login-template.html'
    });

    LoginComponentController.$inject = ['$location', 'authFactory']

    function LoginComponentController($location, authFactory) {
        var lc = this;
        lc.login = login;
        lc.logout = logout;
        
        init();

        function init() {
            authFactory.auth.$onAuthStateChanged(function (user) {
             lc.isLoggedIn = !!user;
             lc.email = user.email;
            });
        }

        function login() {
            authFactory.login(lc.email, lc.password)
                .then(function () {
                    lc.errorMessage = '';
                    $location.path('/quiz/gcp');
                }).catch(function (err) {
                    lc.errorMessage = 'Login failed';
                });
        }


        function logout() {
            authFactory.logout(lc.email, lc.password).then(function () {
                $location.path('/');
            });
        }
    }
})();