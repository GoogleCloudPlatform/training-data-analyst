# 3. Creating compelling dashboards

### Ingest data if necessary
If you didn't go through Chapter 2, the simplest way to get the files you need is to copy it from my bucket:
* Go to the 02_ingest folder of the repo
* Run the program ./ingest_from_crsbucket.sh and specify your bucket name.


### Loading data into Google Cloud SQL
* In CloudShell, change to the 03_sqlstudio directory in your clone of the source code repository.
* Run the script 
  ```./create_instance.sh```
* Go the GCP web console and change the root password of the Cloud SQL instance.
* Create the table by running the script 
  ```
  ./create_table.sh
  ```
  The script will prompt you for the root password of the Cloud SQL instance.
* Populate the table by running the script 
  ```
  ./populate_table.sh  <BUCKET-NAME>
  ```
  Note that this script requires you to pass in your bucket name as a command-line parameter.
  It will prompt you for the root password of your MySQL instance.
* Compute the contingency table for a specific threshold by running the script 
  ```
  ./contingency.sh.
  ```

### Building a dashboard
Follow the steps in the main text of the chapter to set up a Data Studio dashboard and create charts. Once you are done, delete the Cloud SQL instance since you will not need it for the rest of the book.
