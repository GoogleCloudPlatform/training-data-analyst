const router = require('express').Router();
const { API_PREFIX } = require('../constants/global.constant');

router.use(API_PREFIX, require('./api/api.route'));

module.exports = router;
