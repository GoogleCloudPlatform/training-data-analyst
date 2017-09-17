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

    module.factory('authFactory', authFactory);


    authFactory.$inject = ['$q' ,'$firebaseAuth']

    function authFactory($q, $firebaseAuth) {
        var auth = $firebaseAuth();

        var user = {
            isLoggedIn: false,
            email: '',
            uid: -1
        };


        return {
            auth: auth,
            register: register,
            login: login, 
            logout: logout,
            user: user,
            authorize: authorize
        };

        function register(email, password) {
            return auth.$createUserWithEmailAndPassword(email, password).then(function (firebaseUser) {
                user.uid = firebaseUser.uid;
                user.email = email;
                user.isLoggedIn = true;
            });
        }

        function authorize() {
            return user.isLoggedIn ? $q.resolve(user) : $q.reject(user);
        }

        function login(email, password) {
            return auth.$signInWithEmailAndPassword(email, password).then(function (firebaseUser) {
                user.uid = firebaseUser.uid;
                user.email = email;
                user.isLoggedIn = true;
            });
        }

        function logout() {
            return auth.$signOut();
        }
    }


})();