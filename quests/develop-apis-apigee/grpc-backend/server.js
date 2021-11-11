const grpc = require('@grpc/grpc-js');
const protoLoader = require('@grpc/proto-loader');

const admin = require("firebase-admin");
const { toPlainObject } = require('lodash');
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
const BACKENDVER = "2.0.0";

function checkStatus(call, callback) {
	let result;
	result = {
		serviceName: "simplebank-grpc",
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

// ERROR RESPONSES

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

function unknown(message) {
	return {
		code: grpc.status.UNKNOWN,
		message: message
	};
}

function cancelled(message) {
	return {
		code: grpc.status.CANCELLED,
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
	console.log(`buildAtm: ${JSON.stringify(data)})`);
	let result;
	let latitude;
	let longitude;
	if (data.location) {
		latitude = data.location.latitude;
		longitude = data.location.longitude;
		console.log(`in location: ${latitude},${longitude}`);
	} else {
		latitude = data.latitude;
		longitude = data.longitude;
		console.log(`not in location: ${latitude},${longitude}`);
	}
	result = {
		name: data.name,
		location: {
			latitude: latitude,
			longitude: longitude
		},
		description: data.description
	};
	console.log(`result: ${JSON.stringify(result)}`);
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
	if (!ATM_NAME_REGEX.test(name)) {
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
		var atm = buildAtm(data);
		results.push(atm);
		console.log(`atm: ${JSON.stringify(atm)})`);
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
	if (!ATM_NAME_REGEX.test(name)) {
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

// ACCOUNTS

function buildAccount(data) {
	//console.log(`account: ${JSON.stringify(data)})`);
	let result;
	result = {
		customerEmail: data.customerEmail,
		name: data.name,
		balance: data.balance,
		overdraftAllowed: data.overdraftAllowed
	};
	return result;
}

async function retrieveAccount(call, callback) {
	const customerEmail = call.request.customerEmail;
	const name = call.request.name;
	if (!customerEmail) {
		return callback(invalidArg('customerEmail missing'));
	}
	if (!EMAIL_REGEX.test(customerEmail)) {
		return callback(invalidArg('customerEmail pattern incorrect'));
	}
	if (!name) {
		return callback(invalidArg('name missing'));
	}
	if (!ACCOUNT_NAME_REGEX.test(name)) {
		return callback(invalidArg('name pattern incorrect'));
	}
	const path = `customers/${customerEmail}/accounts/${name}`;
	const data = await getByPath(path);
	callback(null, buildAccount(data));
}

async function retrieveAllAccounts(call, callback) {
	const customerEmail = call.request.customerEmail;
	if (!customerEmail) {
		return callback(invalidArg('customerEmail missing'));
	}
	if (!EMAIL_REGEX.test(customerEmail)) {
		return callback(invalidArg('customerEmail pattern incorrect'));
	}
	const path = `customers/${customerEmail}/accounts`;
	const accountArray = await getAllByPath(path);
	var results = [];
	_.each(accountArray, function (data) {
		var account = buildAccount(data);
		results.push(account);
		console.log(`account: ${JSON.stringify(account)})`);
	});
	//console.log(`accountList: ${JSON.stringify(results)})`);
	callback(null, { accountList: results });
}

async function createAccount(call, callback) {
	const customerEmail = call.request.customerEmail;
	const name = call.request.name;
	const balance = call.request.balance;
	if (!customerEmail) {
		return callback(invalidArg('customerEmail missing'));
	}
	if (!EMAIL_REGEX.test(customerEmail)) {
		return callback(invalidArg('customerEmail pattern incorrect'));
	}
	if (!name) {
		return callback(invalidArg('name missing'));
	}
	if (name.length > MAX_NAME_LENGTH) {
		return callback(invalidArg(`name may only be up to ${MAX_NAME_LENGTH} characters`));
	}
	if (!ACCOUNT_NAME_REGEX.test(name)) {
		return callback(invalidArg('name pattern incorrect'));
	}
	if (!isValidCurrency(balance) || balance < 0) {
		return callback(invalidArg(`balance must be nonnegative with a maximum of 2 digits after the decimal point`));
	}
	const customerPath = `customers/${customerEmail}`;
	const customerRef = db.doc(path);
	const accountPath = `customers/${customerEmail}/accounts/${name}`;
	const accountRef = db.doc(path);
	const data = buildAccount(call.request);

    try {
        await db.runTransaction(async (t) => {
            // check customer
            const customerDoc = await t.get(customerRef);
            if (customerDoc.exists) {
                console.log(`customer ${customerPath} exists, will add account ${accountPath}`);

                await accountRef.create(data).then((result) => {
					// success
					return callback(null, data);
                }).catch((err) => {
					return callback(alreadyExists('account name for customer already exists'));
                });

            } else {
                // can only create an account for a customer who exists
				return callback(notFound('customer with specified email does not exist'));
            }
        });
    } catch (e) {
        // transaction failure
		return callback(unknown('account creation failure'));
    }
}

// TRANSACTIONS

// defaults to success = false
function buildTransaction(data) {
	console.log(`transaction: ${JSON.stringify(data)})`);
	let result;
	result = {
		customerEmail: data.customerEmail,
		accountName: data.accountName,
		transactionType: data.transactionType,
		amount: data.amount,
		success: false,
		id: data.id
	};
	if (data.failureMessage != "") {
		result.failureMessage = data.failureMessage;
	}
	if (data.transactionType == TRANSFER) {
		console.log("it is a transfer");
		result.toCustomerEmail = data.toCustomerEmail;
		result.toAccountName = data.toAccountName;
	}
	return result;
}

async function retrieveTransaction(call, callback) {
	const id = call.request.id;
	if (!id) {
		return callback(invalidArg('id missing'));
	}
	const path = `transactions/${id}`;
	const data = await getByPath(path);
	callback(null, buildTransaction(data));
}

async function retrieveAllTransactions(call, callback) {
	const path = `transactions`;
	const transactionArray = await getAllByPath(path);
	var results = [];
	_.each(transactionArray, function (data) {
		var transaction = buildTransaction(data);
		results.push(transaction);
		console.log(`transaction: ${JSON.stringify(transaction)})`);
	});
	//console.log(`transactionList: ${JSON.stringify(results)})`);
	callback(null, { transactionList: results });
}

async function createTransaction(call, callback) {
	const customerEmail = call.request.customerEmail;
	const accountName = call.request.accountName;
	const transactionType = call.request.transactionType;
	const amount = call.request.amount;
	const toCustomerEmail = call.request.toCustomerEmail;
	const toAccountName = call.request.toAccountName;
	if (!customerEmail) {
		return callback(invalidArg('customerEmail missing'));
	}
	if (!accountName) {
		return callback(invalidArg('accountName missing'));
	}
	if (!isValidTransactionType(transactionType)) {
		return callback(invalidArg(`transactionType must be ${DEPOSIT}, ${WITHDRAWAL}, or ${TRANSFER}.`));
	}
	if (!isValidCurrency(amount) || amount <= 0) {
		return callback(invalidArg(`amount must be positive with a maximum of 2 digits after the decimal point`));
	}
	if (transactionType === TRANSFER && !toCustomerEmail) {
		return callback(invalidArg(`toCustomerEmail missing, required for TRANSFER transactions`));
	}
	if (transactionType === TRANSFER && !toAccountName) {
		return callback(invalidArg(`toAccountName missing, required for TRANSFER transactions`));
	}
	if (transactionType !== TRANSFER && toCustomerEmail.length > 0) {
		return callback(invalidArg(`toCustomerEmail specified, but only allowed for TRANSFER transactions`));
	}
	if (transactionType !== TRANSFER && toAccountName.length > 0) {
		return callback(invalidArg(`toAccountName specified, but only allowed for TRANSFER transactions`));
	}
	const transactionDocRef = db.collection('transactions').doc();
	const transactionDocId = transactionDocRef.id;
	const customerAccountPath = `customers/${customerEmail}/accounts/${accountName}`
	const transactionData = buildTransaction(call.request);
	transactionData.id = transactionDocId;

    console.log(`Creating initial transaction ${transactionDocId}: transactionData=${JSON.stringify(transactionData)}`);
    await transactionDocRef.create(transactionData).then((result) => {
        // success
    }).catch((err) => {
		const errMessage = `transaction ${transactionDocId}: transaction creation failure`;
		return callback(unknown(errMessage));
	});

    console.log(`Starting firestore transaction`);
    try {
        await db.runTransaction(async (t) => {
            // check account
            const accountRef = db.doc(customerAccountPath);
            console.log(`getting account ${customerAccountPath}`);
            const accountDoc = await t.get(accountRef);
            if (!accountDoc.exists) {
                console.log(`account ${customerAccountPath} does not exist`);
                // account must exist
				const errMessage = `source account does not exist`;
				t.update(transactionDocRef, { failureMessage: errMessage });
				return callback(notFound(`transaction ${transactionDocId}: ${errMessage}`));
            }
            var accountData = accountDoc.data();
            console.log(`accountData=${JSON.stringify(accountData)}`);
            var accountBalance = accountData.balance;
            var overdraftAllowed = accountData.overdraftAllowed;
            console.log(`accountData: balance=${accountBalance}, overdraftAllowed=${overdraftAllowed}`);

			var toAccountPath = "";
            var toAccountRef = null;
            var toAccountDoc = null;
            var toAccountData = null;
            if (transactionType === TRANSFER) {
                // to account is required
				toAccountPath = `customers/${toCustomerEmail}/accounts/${toAccountName}`
                toAccountRef = db.doc(toAccountPath);
                toAccountDoc = await t.get(toAccountRef);
                if (!toAccountDoc.exists) {
                    // to account must exist
					const errMessage = `destination account does not exist`;
					t.update(transactionDocRef, { failureMessage: errMessage });
					return callback(notFound(`transaction ${transactionDocId}: ${errMessage}`));
                }
                toAccountData = toAccountDoc.data();
            }

            // get transaction doc (GET required for a firestore transaction)
            const transactionDoc = await t.get(transactionDocRef);
            var transactionDocData = transactionDoc.data();

            var balanceChange;
            if (transactionType === TRANSFER || transactionType === WITHDRAWAL) {
                balanceChange = -amount;

                // check for overdraft
                if (!overdraftAllowed && amount > accountBalance) {
                    // would be overdraft
					const errMessage = `insufficient funds`;
					t.update(transactionDocRef, { failureMessage: errMessage });
					return callback(cancelled(`transaction ${transactionDocId}: ${errMessage}`));
                }

                t.update(accountRef, {
                    balance: admin.firestore.FieldValue.increment(balanceChange)
                });
                if (transactionType === TRANSFER) {
                    t.update(toAccountRef, {
                        balance: admin.firestore.FieldValue.increment(-balanceChange)
                    });
                }
            } else { // DEPOSIT
                balanceChange = amount;
                console.log(`depositing ${amount} into account ${account}`);

                t.update(accountRef, {
                    balance: admin.firestore.FieldValue.increment(balanceChange)
                });
                console.log(`deposited ${amount} into account ${account}`);
            }

            transactionDocData.success = true;
            console.log(`updating transaction ${transactionDocId} with success`);
            t.update(transactionDocRef, { success: true, id: transactionDocId });
			return callback(null, transactionDocData);
        });
    } catch (e) {
        // transaction failure
		return callback(unknown('transaction creation failure'));
    }
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
		CreateAtm: createAtm,
		RetrieveAccount: retrieveAccount,
		RetrieveAllAccounts: retrieveAllAccounts,
		CreateAccount: createAccount,
		RetrieveTransaction: retrieveTransaction,
		RetrieveAllTransactions: retrieveAllTransactions,
		CreateTransaction: createTransaction
	});
	server.bindAsync(`0.0.0.0:${PORT}`, grpc.ServerCredentials.createInsecure(), (error, port) => {
		if (error) {
			throw error;
		}
		server.start();
	});
}

main();