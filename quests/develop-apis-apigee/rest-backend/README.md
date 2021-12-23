SimpleBank REST service

GET /customers - retrieve all customers
GET /customers/{id} - retrieve a single customer by ID (email address)
POST /customers - create a customer
PUT /customers/{id} - modify a customer

GET /atms - retrieve all ATMs
GET /atms/{id} - retrieve a single ATM by ID (name)
POST /atms - create an ATM
PUT /atms/{id} - modify an ATM

GET /customers/{customerEmail}/accounts - retrieve all accounts for a customer
GET /customers/{customerEmail}/accounts/{accountId} - retrieve a single customer account by name
POST /customers/{customerEmail}/accounts - create an account for a customer

GET /transactions - retrieve all transactions
GET /transactions/{id} - retrieve a transaction by ID
POST /transactions - create a transaction