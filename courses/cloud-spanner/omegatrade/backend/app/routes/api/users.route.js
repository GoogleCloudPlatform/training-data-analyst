const router = require('express').Router();
const UserController = require('../../controller/user.controller');
router.post('/register-user', UserController.register);
router.post('/login', UserController.login);
router.post('/google-sign-in', UserController.googleSignIn);
router.post('/change-password', UserController.changePassword);
module.exports = router;
