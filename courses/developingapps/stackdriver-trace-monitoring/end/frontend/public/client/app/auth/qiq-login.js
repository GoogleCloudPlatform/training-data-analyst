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
        lc.user = authFactory.user
        init();

        function init() {
            lc.isLoggedIn = !!lc.user;
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
        }
    }
})();