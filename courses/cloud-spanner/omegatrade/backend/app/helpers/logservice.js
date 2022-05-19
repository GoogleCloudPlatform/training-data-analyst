const filename = `${process.cwd()}/logs/error.log`;
const log = require('simple-node-logger').createSimpleFileLogger(filename);
const writeLog = async (context, error) => {
    const { message, code, stack } = error;
    log.setLevel('all');
    log.error(`Error Occured in ${context} - ErroCode : ${code} - message: ${message}`);
    log.trace(stack);
}
module.exports = { writeLog }