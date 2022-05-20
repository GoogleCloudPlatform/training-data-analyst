const express = require('express');
const bodyparser = require('body-parser');
const dotenv = require('dotenv');
var cors = require('cors');

const app = express();
dotenv.config();
app.use(cors())

app.use(bodyparser.urlencoded({ extended: false }));
app.use(bodyparser.json());
app.use(require('./app/routes/index.route'));
port = process.env.PORT || 3000;

app.listen(port, () => {
    console.log(`STOCK APP listening at http://localhost:${port}`)
});


