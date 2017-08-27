const Pubsub = require('@google-cloud/pubsub');
const config = require('../config');

const topicName = config.get('TOPIC_NAME');
const subscriptionName = config.get('SUBSCRIPTION_NAME');

const pubsub = Pubsub({
  projectId: config.get('GCLOUD_PROJECT')
});



// [START create]
function create({ quiz, author, title, answer1, answer2, answer3, answer4, correctAnswer, imageUrl }) {

  const key = ds.key(kind);

  const entity = {
    key,
    data: [
      { name: 'quiz', value: quiz },
      { name: 'author', value: author },
      { name: 'title', value: title },
      { name: 'answer1', value: answer1 },
      { name: 'answer2', value: answer2 },
      { name: 'answer3', value: answer3 },
      { name: 'answer4', value: answer4 },
      { name: 'correctAnswer', value: correctAnswer },
      { name: 'imageUrl', value: imageUrl },
    ]
  };
  return ds.save(entity);
}
// [END create]

// [START exports]
module.exports = {
  create,
  list
};
// [END exports]
