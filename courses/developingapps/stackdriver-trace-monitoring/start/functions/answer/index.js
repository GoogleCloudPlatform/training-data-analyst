const answerStorage = require('./spanner');
/**
 * Triggered from a message on a Cloud Pub/Sub topic.
 *
 * @param {!Object} event The Cloud Functions event.
 * @param {!Function} The callback function.
 */

exports.subscribe = function subscribe(event) {
  // The Cloud Pub/Sub Message object.
  const pubsubMessage = event.data;

  let answerObject = JSON.parse(Buffer.from(pubsubMessage.data, 'base64').toString()).data;
  console.log('Answer object data:' + JSON.stringify(answerObject));
  
  return answerStorage.saveAnswer(answerObject).then(() => {
  	console.log('answer saved...');
  	return 'success';
  	
  }).catch(console.error);
  
};


