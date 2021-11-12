# 2. Ingesting data onto the Cloud

### Create a bucket
* Go to the Storage section of the GCP web console and create a new bucket

### Populate your bucket with the data you will need for the book
The simplest way to get the files you need is to copy it from my bucket:
* Go to the 02_ingest folder of the repo
* Run the program ./ingest_from_crsbucket.sh and specify your bucket name.

Alternately, you can ingest from the original source of the data and carry out the cleanup steps as described in the text:
* Go to the 02_ingest folder of the repo
* Change the BUCKET variable in upload.sh
* Execute ./ingest.sh
* Execute monthlyupdate/ingest_flights.py specifying your bucket name, and with year of 2016 and month of 01.  Type monthlyupdate/ingest_flights.py --help to get usage help.
This will initialize your bucket with the input files corresponding to 2015 and January 2016. These files are needed to carry out the steps that come later in this book.

### [Optional] Scheduling monthly downloads
* Go to the 02_ingest/monthlyupdate folder in the repo.
* Generate a new Personal Access Token by running ./generate_token.sh -- Note the token printed.
* Modify main.py to have this token.</p>
* Deploy Cloud Function in your project by running ./deploy_cf.sh -- Note the URL that is printed.
* Try out ingest by running ./call_cf.sh supplying the necessary parameters.</p>
* Schedule ingest by running ./setup_cron.sh supplying the necessary parameters.
* Visit the GCP Console for Cloud Functions and Cloud Scheduler and delete the function and the scheduled task—you won’t need them any further.
