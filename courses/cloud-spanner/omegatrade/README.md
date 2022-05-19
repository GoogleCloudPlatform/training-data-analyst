# OmegaTrade App

Omega Trade is a Sample application for [Spanner Terraform Example](https://github.com/cloudspannerecosystem/spanner-terraform-example).  
This project was built using [Angular CLI](https://github.com/angular/angular-cli) version 11.0.0 and [Express](https://github.com/expressjs/express/blob/master/Readme.md) (Node.js web application framework) version 4.17.0.

## Dependencies
* Install [Node](https://nodejs.org/en/download/) version >= 10.16 and [NPM](https://nodejs.org/en/download/) version >= 6.9
* Cloud Spanner - [emulator](https://cloud.google.com/spanner/docs/emulator)
  * The emulator is included in the [Google Cloud SDK](https://cloud.google.com/sdk)
and can be invoked via the [gcloud emulators spanner](https://cloud.google.com/sdk/gcloud/reference/emulators/spanner) commands. 
  * Please [install](https://cloud.google.com/sdk/docs/install) Cloud SDK before proceeding further, if you haven't already. 
* Cloud Spanner - [Node.js Client](https://www.npmjs.com/package/@google-cloud/spanner)
  * This package would be installed through `npm install` command while setting up backend services as a part of [Step 2](https://github.com/cloudspannerecosystem/omegatrade#2-setup-backend).

## Quickstart

The following steps will guide you to run the OmegaTrade application locally.

1. Set up the Cloud Spanner emulator and create the instance, database and schema in the emulator.
2. Set up the Backend service and connect it to the emulator. 
3. Seed sample data in the OmegaTrade app.
4. Set up the Frontend service and configure the API base URL.
5. Run the OmegaTrade app.
6. (Optional) Configure Google OAuth in frontend to enable sign-in with your Google account.

## 1. Emulator Setup

There are various options to start the emulator locally. Here we will cover the gcloud instructions. All other methods can be found within the Cloud Spanner Emulator [GitHub repository](https://github.com/GoogleCloudPlatform/cloud-spanner-emulator/blob/master/README.md#quickstart). 

Via gcloud commands

```
gcloud components update 
gcloud emulators spanner start 
```
The following commands will create a configuration for the emulator. This is a one-time setup and can be reused subsequently.
Open a new terminal and run the following commands

```
gcloud config configurations create emulator
gcloud config set auth/disable_credentials true
gcloud config set project test-project
gcloud config set api_endpoint_overrides/spanner http://localhost:9020/
```

Upon running above commands successfully, activate the emulator configuration

```
gcloud config configurations activate emulator
```

Validate your emulator is configured correctly

```
gcloud config list
```

Let’s create an instance, database and tables on the local emulator. 

#### Create an instance in the emulator 

```
gcloud spanner instances create omegatrade-instance --config=emulator-config --description="OmegaTrade Instance - Cloud Spanner Emulator" --nodes=3
```

#### Create a database

```
gcloud spanner databases create omegatrade-db --instance omegatrade-instance
```

#### Create tables 

```
gcloud spanner databases ddl update omegatrade-db --instance omegatrade-instance --ddl "CREATE TABLE users (userId STRING(36) NOT NULL, businessEmail STRING(50), fullName STRING(36), password STRING(100), photoUrl STRING(250), provider STRING(20), forceChangePassword BOOL) PRIMARY KEY(userId); CREATE UNIQUE NULL_FILTERED INDEX usersByBusinessEmail ON users (businessEmail);"
```
```
gcloud spanner databases ddl update omegatrade-db --instance omegatrade-instance --ddl "CREATE TABLE companies (companyId STRING(36) NOT NULL, companyName STRING(30), companyShortCode STRING(15), created_at TIMESTAMP NOT NULL OPTIONS (allow_commit_timestamp=true)) PRIMARY KEY(companyId);"
```
```
gcloud spanner databases ddl update omegatrade-db --instance omegatrade-instance --ddl "CREATE UNIQUE NULL_FILTERED INDEX companiesByCompanyName ON companies (companyName); CREATE UNIQUE NULL_FILTERED INDEX companiesByShortCode ON companies (companyShortCode);"
```
```
gcloud spanner databases ddl update omegatrade-db --instance omegatrade-instance --ddl "CREATE TABLE companyStocks (companyStockId STRING(36) NOT NULL, companyId STRING(36) NOT NULL, open NUMERIC, volume NUMERIC, currentValue NUMERIC, date FLOAT64, close NUMERIC, dayHigh NUMERIC, dayLow NUMERIC, timestamp TIMESTAMP NOT NULL OPTIONS (allow_commit_timestamp=true), CONSTRAINT FK_CompanyStocks FOREIGN KEY (companyId) REFERENCES companies (companyId)) PRIMARY KEY(companyStockId);"
```
```
gcloud spanner databases ddl update omegatrade-db --instance omegatrade-instance --ddl "CREATE TABLE simulations (sId STRING(36) NOT NULL, companyId STRING(36) NOT NULL, status STRING(36), createdAt TIMESTAMP NOT NULL OPTIONS (allow_commit_timestamp=true), CONSTRAINT FK_CompanySimulation FOREIGN KEY (companyId) REFERENCES companies (companyId)) PRIMARY KEY(sId);"
```

Run the following command on emulator instance to check the table creation.

```
gcloud spanner databases execute-sql omegatrade-db  --instance=omegatrade-instance  --sql='SELECT * FROM information_schema.tables WHERE table_schema <> "INFORMATION_SCHEMA"'
```

## 2. Set up the Backend

Now, the emulator is up and running. Let’s clone this repo and run the backend service of OmegaTrade with the emulator. 

```
git clone https://github.com/cloudspannerecosystem/omegatrade.git
cd omegatrade/backend
```

Install dependencies in the `backend` folder

```
npm install 
```

Create .env file in the `backend` folder (if not already exists) and ensure the **Project ID**, **Instance** and **Database** name match the ones we created above. 

```
PROJECTID = test-project
INSTANCE = omegatrade-instance
DATABASE = omegatrade-db
JWT_KEY = w54p3Y?4dj%8Xqa2jjVC84narhe5Pk
EXPIRE_IN = 2d
```

```
export SPANNER_EMULATOR_HOST="localhost:9010"
node server.js
```

The above command will run the Backend service in `http://localhost:3000`

## 3. Seed Sample Data

Open a new terminal and go back to the `backend` folder. Run the below commands:

```
export SPANNER_EMULATOR_HOST="localhost:9010"
node seed-data.js 
```
The above command will migrate sample data into the connected database.
If the seeding was successful, you will get a `Data Loaded successfully` message.

Note: You may run this migration only on an empty database, to avoid duplication.

## 4. Set up the Frontend

Now let's run the frontend service of OmegaTrade.

```
cd .. && cd frontend

#Install Dependencies
npm install 
```

Now let's configure the client ID and backend API url.

```
cd src/environments
vi environment.ts
```

Change the **base URL** according to the **backend URL** (ensure you append the /api/v1/ as below)

```
export const environment = {
  production: false,
  name: "dev",
  // change baseUrl according to backend URL
  baseUrl: "http://localhost:3000/api/v1/", 
  clientId: ""
};
```

## 5. Run the Application

Go back to the frontend folder.

Run `npm start` in the `frontend` folder. This command will serve the whole application and it will start running in the URL `http://localhost:4200`. 

## 6. (Optional) Configure Google OAuth in Frontend

Google OAuth enables you to sign in with your Google account directly from the application. Here are the steps you need to follow in order to use this service.

#### Creating Omega Trade application in the OAuth Consent screen for the first time.

1. Go to the [OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent).
2. Choose the user type as either Internal or External and click create.
3. Add your application name (i.e OmegaTrade) in the App name field.
4. Choose your email in the User support email section.
5. Add your email in developer contact information.  
6. Add your organization's app domain and authorized domain, if you do not have both you can skip this step.
7. Click save and continue.
8. Add Scopes if you want and continue with next steps.
9. Save your changes.

#### Modifying OAuth Consent Screen application.

The following steps are required only if you want to modify the name of existing application to OmegaTrade.

1. Go to the [OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent).
2. Click on the Edit App button. 
3. Replace the existing application name with "OmegaTrade" in the App name field.
4. Choose your email in the User support email section.
5. Add your email in developer contact information.
6. Add your organization's app domain and authorized domain, if you do not have both you can skip this step.
7. Click save and continue. 
8. Add Scopes if you want and continue with the following steps.
9. Save your changes.

#### Creating Google OAuth credentials

The following steps will guide you to create OAuth Credentials for the registered application.

1. Go to the [Google API Console Credentials](https://console.developers.google.com/apis/credentials). Click on Create Credentials and choose OAuth client ID. 

2. Choose Web Application in the application type and enter the name of your choice.    

3. Add frontend URL i.e. `http://localhost:4200` (from step 5) in Authorized JavaScript origins **ADD URI** section and click on create button. Copy your client id from the popup window.

4. Now we need to update the Client ID in the `environment.ts` file of frontend folder.

```
cd src/environments
vi environment.ts
```

Update the **clientId** as below.

```
export const environment = {
  production: false,
  name: "dev",
  // change baseUrl according to backend URL
  baseUrl: "http://localhost:3000/api/v1/", 
  // change clientId to actual value you have received from Oauth console 
  clientId: "142706365772-ol2a8hcqs1d3rrgjgvxxxxxxxxdqpog8.apps.googleusercontent.com"
};
```

NOTE: Please ensure that cookies are enabled in your browser to avoid being blocked from running the app. The official OAuth setup guide can also be found [here](https://support.google.com/cloud/answer/6158849?hl=en#zippy=).


Now Angular will automatically detect your changes and serve the app in `http://localhost:4200` URL.
