To try out the use of a private key JSON:

* Create a GCE instance *without* full access to gcloud. Notice that the creation menu asks for the service account and the defaults to projectnumber-compute@developer.gserviceaccount.com
    * Wait for ~60s for lock on /var/lib/dpkg to get releasedf
    * sudo apt-get install -y git python-pip
    * git clone https://github.com/GoogleCloudPlatform/training-data-analyst
    * cd training-data-analyst/blogs/pandas-pvtkey
    * ./install.sh
* run query.py or pkg_query.py
    * Edit the file to set the project id appropriately
    * Run query.py
    * It will <b>fail</b> saying a key wasn't found
* In the GCP web console, navigate to IAM > Service Accounts and create a private key for the Compute Engine and upload to the specified location
* run query.py or pkg_query.py
    It will work now. 

Note: If the last step fails with an error saying "Invalid JWT Signature.", you might need to enable the IAM API in the APIs and Services of the GCP web console
