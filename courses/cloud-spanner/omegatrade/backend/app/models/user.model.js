'use strict';
const database = require('./../config/database.js');
var User = function () { };

User.registerUser = async function (user) {
  return await database.table('users').insert(user);
}

User.findUser = async function (email) {
  const [user] = await database.run({
    sql: 'SELECT userId, fullName, businessEmail, password, photoUrl, provider FROM users WHERE businessEmail = @businessEmail',
    params: {
      businessEmail: email
    },
    json: true,
  });
  return user;
}

User.update = async function (userObj) {
  return await database.table('users').update([userObj]);
}

User.findById = async function(userId){
  const [user] = await database.table('users').read({
    columns: ['userId', 'fullName', 'businessEmail', 'photoUrl', 'provider'],
    keys: [userId],
    json: true
  });
  return user;
}

module.exports = User
