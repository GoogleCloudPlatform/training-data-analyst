const router = require('express').Router();
router.use('/users', require('./users.route'));
router.use('/companies', require('./companies.route'));
router.use('/simulations', require('./simulations.route'));

router.use((err, req, res, next) => {
    if (err.name === 'ValidationError') {
      return res.status(422).json({
        errors: Object.keys(err.errors).reduce((errors, key) => {
          errors[key] = err.errors[key].message; // eslint-disable-line
          return errors;
        }, {}),
      });
    }
    return next(err);
  });
  
  module.exports = router;