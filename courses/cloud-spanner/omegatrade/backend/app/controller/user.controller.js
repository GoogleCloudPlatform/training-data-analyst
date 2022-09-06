'use strict';
const User = require('../models/user.model')
const bcrypt = require('bcryptjs')
const jwt = require("jsonwebtoken");
const { v4: uuidv4 } = require('uuid');
const logService = require('../helpers/logservice');


/**
 * Function to create a new user if not exists
 * @method POST
 * @param {JSON} req contains request headers and payload businessEmail,fullName,password,photoUrl,provider
 */
exports.register = async function (req, res) {
    try {
        const body = req.body;
        const [registerUser] = await User.findUser(body.businessEmail);
        if (registerUser && registerUser.userId) {
            return res.status(409).json({ success: false, message: 'Registration failed, email already exists!' });
        }
        const salt = await bcrypt.genSalt(10);
        const password = await bcrypt.hash(body.password, salt);

        // deleting password and confirm password as both are not required to store
        delete body.password;
        delete body.confirmPassword;

        const user = { ...body, userId: uuidv4() };
        await User.registerUser({ ...user, password });
        jwt.sign(user, process.env.JWT_KEY, { expiresIn: process.env.EXPIRE_IN }, function (err, token) {
            if (err) {
                return res.status(500).json({ success: false, message: 'Something went wrong while registering a new user!' });
            }
            return res.status(200).json({ success: true, message: 'Registered successfully!', userInfo: user, authToken: token });
        });
    } catch (error) {
        logService.writeLog('user.controller.register', error);
        return res.status(500).json({ success: false, message: 'Something went wrong while registering a new user!' });
    }
};

/**
 * Function to validate and login user.
 * @method POST
 * 
 * @param {*} req contains request headers and payload businessEmail,password
 */
exports.login = async function (req, res) {
    try {
        const body = req.body;
        const [user] = await User.findUser(body.businessEmail);
        if (user && user.userId) {
            if (bcrypt.compareSync(body.password, user.password)) {
                delete user.password;
                const token = jwt.sign(user, process.env.JWT_KEY, {
                    expiresIn: process.env.EXPIRE_IN
                });
                return res.status(200).json({ success: true, message: 'Logged in successfully.', userInfo: user, authToken: token });
            } else {
                return res.status(409).json({ success: false, message: 'Login failed.' });
            }
        } else {
            return res.status(409).json({ success: false, message: 'Please register your account before login!' });
        }
    } catch (error) {
        logService.writeLog('user.controller.login', error);
        return res.status(500).json({ success: false, message: 'Something went wrong, error while authenticating user!' });
    }
};

/**
 * Function to verify and link Google-User if user already exists,
 * else store a new user in users table with random password. 
 * @method POST
 * 
 * @param {*} req contains request headers and payload businessEmail,password,provider,photoUrl
 */
exports.googleSignIn = async function (req, res) {
    try {
        const body = req.body;
        const [user] = await User.findUser(body.email)
        if (user && user.userId) {
            // updating provider and photoUrl only if user did not registered with Google before
            if (user.provider === '' || user.provider === null) {
                user.provider = body.provider;
                user.photoUrl = body.photoUrl;
                await User.update(user)
            } 
            const token = jwt.sign(user, process.env.JWT_KEY, {
                expiresIn: process.env.EXPIRE_IN
            });
            return res.status(200).json({ success: true, message: 'Logged in successfully', userInfo: user, authToken: token });
        } else {
            const salt = await bcrypt.genSalt(10);
            // generating random password as password field should not empty.
            const randomPassword = Math.random().toString(36).slice(-6);
            const password = await bcrypt.hash(randomPassword, salt);
            const user = {
                userId: uuidv4(),
                businessEmail: body.email,
                fullName: body.name,
                password: password,
                photoUrl: body.photoUrl,
                provider: body.provider,
                forceChangePassword: true
            };
            await User.registerUser(user);
            jwt.sign(user, process.env.JWT_KEY, { expiresIn: process.env.EXPIRE_IN }, function (err, token) {
                if (err) {
                    return res.status(500).json({ success: false, message: 'Something went wrong while registering new user!' });
                }
                return res.status(200).json({ success: true, message: 'Registered successfully!', userInfo: user, authToken: token });
            });
        }
        
    } catch (error) {
        logService.writeLog('user.controller.googleSignIn', error);
        return res.status(500).json({ success: false, message: 'Something went wrong, error while authenticating user!' });
    }
};

exports.changePassword = async function (req, res) {
    try {
        const body = req.body;
        const [user] = await User.findById(body.userId)
        if (user) {
            const salt = await bcrypt.genSalt(10);
            user.password = await bcrypt.hash(body.password, salt);
            user.forceChangePassword = false;
            await User.update(user)
            return res.status(200).json({ success: true, message: 'Password changed successfully', user: user });
        } else {
            return res.json({ success: false, message: 'Invalid data, please check the details you have entered.' });
        }
    } catch (error) {
        logService.writeLog('user.controller.changePassword', error);
        return res.status(500).json({ success: false, message: 'Something went wrong, error while attempting to change the password.' });
    }
}
