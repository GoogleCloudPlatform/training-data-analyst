## Earthquake VM Demo

* From the Compute Engine section of the Cloud Console, 
choose VM instances and create a new virtual machine.
* Select 2 vCPUs and make sure to select "Allow full access to all Cloud APIs"
* SSH to the new instance.
* In the terminal, install git so that you can clone the source repository:
```
sudo apt-get -y install git
```
* Then, clone the source repository:
```
git clone https://github.com/GoogleCloudPlatform/training-data-analyst
```
* Go to the directory containing demo files and install python packages we need:
```
cd training-data-analyst/courses/bdml_fundamentals/demos/earthquakevm
./install_missing.sh
```
* Now, ingest data on recent earthquakes from the USGS:
```
./ingest.sh
```
* Transform the raw data into an image:
```
./transform.py
```
* Go to the Storage | Browser in the Cloud Console and create a new bucket
* Copy the files to the bucket:
```gsutil cp earthquakes.* gs://[YOURBUCKET]```
* Refresh the Storage | Browser to verify that you have new files in Cloud Storage
* Edit the bucket permissions and add a new member named ```allUsers``` 
and give this member Cloud Storage Object Viewer permissions
* Visit https://storage.googleapis.com/BUCKET/earthquakes.htm
