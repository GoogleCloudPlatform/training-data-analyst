const jwt = require('jsonwebtoken');

module.exports = {
    validateToken: (req, res, next) => {
        const authorizationHeader = req.headers.authorization;
        if (authorizationHeader) {
            const token = authorizationHeader.split(' ')[1]; // Bearer <token>
            if (token === null) {
                return res.status(401).send({ message: `Authentication error`, success: false });
            }
            const options = {
                expiresIn: process.env.EXPIRE_IN
            };
            jwt.verify(token, process.env.JWT_KEY, options, async (err, result) => {
                if (err) {
                    return res.status(401).send({ message: `Session expired, please try to login again.`, success: false });
                }
                if (result) {
                    req.decoded = result;
                    return next();
                }
            });
        } else {
            return res.status(401).send({ message: `Authentication error. Token required.`, success: false });
        }
    }
};