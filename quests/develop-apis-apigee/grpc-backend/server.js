const grpc = require('@grpc/grpc-js');
const protoLoader = require('@grpc/proto-loader');

const admin = require("firebase-admin");
const _ = require("lodash");

admin.initializeApp({
    credential: admin.credential.applicationDefault()
});

var PROTO_PATH = __dirname + '/simplebank.proto';
const packageDefinition = protoLoader.loadSync(
    PROTO_PATH,
    {keepCase: true,
     longs: String,
     enums: String,
     defaults: true,
     oneofs: true
    });

const simplebank = grpc.loadPackageDefinition(packageDefinition).simplebank;

const PORT = process.env.PORT;

function isValidCurrency(input) {
    if (input === undefined) { return true; }
    return (input * 100) % 1 === 0
}

const DEPOSIT = 'DEPOSIT';
const WITHDRAWAL = 'WITHDRAWAL';
const TRANSFER = 'TRANSFER';
function isValidTransactionType(input) {
    if (input === undefined) { return true; }
    switch (input) {
        case DEPOSIT:
        case WITHDRAWAL:
        case TRANSFER:
            return true;
    }
    return false;
}

const EMAIL_REGEX = /[^@\s]+@[^@\s\.]+\.[^@\.\s]+/;
const ATM_NAME_REGEX = /[A-Za-z][A-Za-z0-9]*(-[A-Za-z0-9]+)*/;
const ACCOUNT_NAME_REGEX = /[A-Za-z][A-Za-z0-9]*(-[A-Za-z0-9]+)*/;

const MAX_NAME_LENGTH = 50;
const MAX_DESC_LENGTH = 200;
const MIN_LATITUDE = -90.0;
const MAX_LATITUDE = 90.0;
const MIN_LONGITUDE = -180.0;
const MAX_LONGITUDE = 180.0;

const db = admin.firestore();
const BACKENDVER = "1.0.0";

function checkStatus(call, callback) {
	let result;
	result = {
		serviceVersion: BACKENDVER,
		status: "UP"
	};
	callback(null, result);
}

async function getByPath(path) {
    var docRef = db.doc(path);
    var doc = await docRef.get();
	if (!doc.exists) {
		//console.log(`doc ${path} not found`);
		return {};
	} else {
		//console.log(`doc ${path} FOUND: ${JSON.stringify(doc.data())}`);
		return doc.data();
	}
}

async function getAllByPath(path) {
    var snapshot = await db.collection(path).get();
    var docArray = [];
    snapshot.forEach(doc => {
        docArray.push(doc.data());
    });
	//console.log(`getAllByPath ${path}: ${JSON.stringify(docArray)}`);
    return docArray;
}

function invalidArg(message) {
	return {
		code: grpc.status.INVALID_ARGUMENT,
		message: message
	};
}

function alreadyExists(message) {
	return {
		code: grpc.status.ALREADY_EXISTS,
		message: message
	};
}

function notFound(message) {
	return {
		code: grpc.status.NOT_FOUND,
		message: message
	};
}

// CUSTOMER

function buildCustomer(data) {
	//console.log(`customer: ${JSON.stringify(data)})`);
	let result;
	result = {
		email: data.email,
		firstName: data.firstName,
		lastName: data.lastName
	};
	return result;
}

async function retrieveCustomer(call, callback) {
	const email = call.request.email;
	if (!email) {
		return callback(invalidArg('email missing'));
	}
	if (!EMAIL_REGEX.test(email)) {
		return callback(invalidArg('email pattern incorrect'));
	}
	const path = `customers/${email}`;
	const data = await getByPath(path);
	callback(null, buildCustomer(data));
}

async function retrieveAllCustomers(call, callback) {
	const path = `customers`;
	const customerArray = await getAllByPath(path);
	var results = [];
	_.each(customerArray, function (data) {
		results.push(buildCustomer(data));
		console.log(`customer: ${JSON.stringify(data)})`);
	});
	//console.log(`customerList: ${JSON.stringify(results)})`);
	callback(null, { customerList: results });
}

async function createCustomer(call, callback) {
	const email = call.request.email;
	const lastName = call.request.lastName;
	const firstName = call.request.firstName;
	if (!email) {
		return callback(invalidArg('email missing'));
	}
	if (!EMAIL_REGEX.test(email)) {
		return callback(invalidArg('email pattern incorrect'));
	}
	if (firstName && firstName.length > MAX_NAME_LENGTH) {
		return callback(invalidArg(`firstName may only be up to ${MAX_NAME_LENGTH} characters`));
	}
	if (lastName && lastName.length > MAX_NAME_LENGTH) {
		return callback(invalidArg(`lastName may only be up to ${MAX_NAME_LENGTH} characters`));
	}
	const path = `customers/${email}`;
	const docRef = db.doc(path);
	const data = buildCustomer(call.request);
    await docRef.create(data).then((result) => {
        // success
        return callback(null, data);
    }).catch((err) => {
		return callback(alreadyExists('customer with specified email already exists'));
    });
}

async function updateCustomer(call, callback) {
	const email = call.request.email;
	const lastName = call.request.lastName;
	const firstName = call.request.firstName;
	if (!email) {
		return callback(invalidArg('email missing'));
	}
	if (!EMAIL_REGEX.test(email)) {
		return callback(invalidArg('email pattern incorrect'));
	}
	if (!firstName && !lastName) {
		return callback(invalidArg('firstName or lastName must be specified'));
	}
	if (firstName && firstName.length > MAX_NAME_LENGTH) {
		return callback(invalidArg(`firstName may only be up to ${MAX_NAME_LENGTH} characters`));
	}
	if (lastName && lastName.length > MAX_NAME_LENGTH) {
		return callback(invalidArg(`lastName may only be up to ${MAX_NAME_LENGTH} characters`));
	}
	const path = `customers/${email}`;
	const docRef = db.doc(path);
	const data = buildCustomer(call.request);
    await docRef.update(data).then((result) => {
        // success
        return callback(null, data);
    }).catch((err) => {
		return callback(notFound('customer with specified email does not exist'));
    });
}

// ATM

function buildAtm(data) {
	//console.log(`buildAtm: ${JSON.stringify(data)})`);
	let result;
	let latitude;
	let longitude;
	if (data.location) {
		latitude = data.location.latitude;
		longitude = data.location.longitude;
	} else {
		latitude = data.latitude;
		longitude = data.longitude;
	}
	result = {
		name: data.name,
		location: {
			latitude: latitude,
			longitude: longitude
		},
		description: data.description
	};
	return result;
}

function buildStoredAtm(data) {
	//console.log(`buildStored: ${JSON.stringify(data)})`);
	let result;
	let latitude;
	let longitude;
	if (data.location) {
		latitude = data.location.latitude;
		longitude = data.location.longitude;
	} else {
		latitude = data.latitude;
		longitude = data.longitude;
	}
	result = {
		name: data.name,
		latitude: latitude,
		longitude: longitude,
		description: data.description
	};
	return result;
}

async function retrieveAtm(call, callback) {
	const name = call.request.name;
	if (!name) {
		return callback(invalidArg('name missing'));
	}
	if (!ATM_NAME_REGEX.test(email)) {
		return callback(invalidArg('name pattern incorrect'));
	}
	const path = `atms/${name}`;
	const data = await getByPath(path);
	callback(null, buildAtm(data));
}

async function retrieveAllAtms(call, callback) {
	const path = `atms`;
	const atmArray = await getAllByPath(path);
	var results = [];
	_.each(atmArray, function (data) {
		results.push(buildAtm(data));
		console.log(`atm: ${JSON.stringify(data)})`);
	});
	//console.log(`atmList: ${JSON.stringify(results)})`);
	callback(null, { atmList: results });
}

async function createAtm(call, callback) {
	const name = call.request.name;
	const location = call.request.location;
	const description = call.request.description;
	if (!name) {
		return callback(invalidArg('name missing'));
	}
	if (!ATM_NAME_REGEX.test(email)) {
		return callback(invalidArg('name pattern incorrect'));
	}
	if (!location) {
		return callback(invalidArg('location missing'));
	}
	const latitude = call.request.location.latitude;
	const longitude = call.request.location.longitude;
	if (latitude && (latitude < MIN_LATITUDE || latitude > MAX_LATITUDE)) {
		return callback(invalidArg(`latitude must be between ${MIN_LATITUDE} and ${MAX_LATITUDE}`));
	}
	if (longitude && (longitude < MIN_LONGITUDE || longitude > MAX_LONGITUDE)) {
		return callback(invalidArg(`longitude must be between ${MIN_LONGITUDE} and ${MAX_LONGITUDE}`));
	}
	if (description && description.length > MAX_DESC_LENGTH) {
		return callback(invalidArg(`description may only be up to ${MAX_DESC_LENGTH} characters`));
	}
	const path = `atms/${name}`;
	const docRef = db.doc(path);
	const data = buildStoredAtm(call.request);
    await docRef.create(data).then((result) => {
        // success
        return callback(null, buildAtm(call.request));
    }).catch((err) => {
		return callback(alreadyExists('ATM with specified name already exists'));
    });
}

function main() {
	var server = new grpc.Server();
	server.addService(simplebank.SimpleBank.service, {
		CheckStatus: checkStatus,
		RetrieveCustomer: retrieveCustomer,
		RetrieveAllCustomers: retrieveAllCustomers,
		CreateCustomer: createCustomer,
		UpdateCustomer: updateCustomer,
		RetrieveAtm: retrieveAtm,
		RetrieveAllAtms: retrieveAllAtms,
		CreateAtm: createAtm
	});
	server.bindAsync(`0.0.0.0:${PORT}`, grpc.ServerCredentials.createInsecure(), (error, port) => {
		if (error) {
			throw error;
		}
		server.start();
	});
}

main();