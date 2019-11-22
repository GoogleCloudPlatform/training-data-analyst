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