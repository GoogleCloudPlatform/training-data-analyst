const languageAPI = require('./languageapi');
const feedbackStorage = require('./spanner');
/**
 * Triggered from a message on a Cloud Pub/Sub topic.
 *
 * @param {!Object} event The Cloud Functions event.
 * @param {!Function} The callback function.
 */

exports.subscribe = function subscribe(event) {
  // The Cloud Pub/Sub Message object.
  const pubsubMessage = event.data;

  let feedbackObject = JSON.parse(Buffer.from(pubsubMessage.data, 'base64').toString()).data;
  console.log('Feedback object data before Language API:' + JSON.stringify(feedbackObject));
  
  return languageAPI.analyze(feedbackObject.feedback).then(score => {
  	console.log(`Score: ${score}`);
  	feedbackObject.score = score;
  	return feedbackObject;
  }).then(feedbackStorage.saveFeedback).then(() => {
  	console.log('feedback saved...');
  	return 'success';
  	
  }).catch(console.error);
  
};


